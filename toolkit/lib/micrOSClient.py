import socket
import select
import re
import time
try:
    from .TerminalColors import Colors as color
except:
    from TerminalColors import Colors as color


class micrOSClient:
    CONN_MAP = {}

    def __init__(self, host, port, pwd=None, dbg=False):
        """
        host: host name / IP address
        port: micrOS server port
        dbg: debug prints on/off (session debug)
        """
        # Connection params
        self.conn = None            # connection object
        self.host = host            # server IP address
        self.port = port            # server port
        self.hostname = None        # server hostname: host or resolve
        self.isconn = False         # object is connected
        self.prompt = None          # server prompt for session data check
        self.preprompt = ""
        self.password = pwd
        # Debug params
        self.dbg = dbg
        self.spacer = 0             # to auto-format connection debug print
        self.avg_reply = [0, 0]     # delta t sum, sum cnt to calculate average communication times
        # Validate and resolve host (IP/Hostname)
        self.__address_manager()

    def __address_manager(self):
        self.dbg_print("[INIT] micrOSClient")
        # Host is valid IP address - self.host is ip address OK
        if micrOSClient.validate_ipv4(self.host):
            # Set hostname by prompt in self.connect()
            return

        # Host is hostname - resolve IP - self.host is not ip NOK
        self.hostname = self.host
        # Retrieve IP address by hostname dynamically
        if micrOSClient.CONN_MAP.get(self.hostname, None) is None:
            self.dbg_print("\t[dhcp] Resolve IP by host name... {}".format(self.host))
            if self.host == "__simulator__":
                # Simulator hack - due to no dhcp available
                self.host = '127.0.0.1'
                self.hostname = 'node01'
            else:
                # * Set self.host to ip address OK
                self.host = socket.getaddrinfo(self.host, self.port)[-1][4][0]
                if micrOSClient.validate_ipv4(self.host):
                    micrOSClient.CONN_MAP[self.hostname] = self.host
                else:
                    self.dbg_print("\tInvalid resolved IP")
                    raise Exception("Invalid host: {}".format(self.host))
        else:
            self.dbg_print("\t[cache] Resolve IP by host name...")
            # * Set self.host to ip address OK
            #       Restore IP from cache by hostname
            self.host = micrOSClient.CONN_MAP[self.hostname]

    @staticmethod
    def validate_ipv4(str_in):
        pattern = "^([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])$"
        if bool(re.match(pattern, str_in)):
            return True
        return False

    def __connect(self, timeout):
        # Server connection - create socket
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.settimeout(timeout)

        # Server connection - connect
        self.conn.connect((self.host, self.port))
        # Store connection state
        self.isconn = True

    def connect(self, timeout, retry=5):
        """
        Connect to server and wait for prompt
        - save connection state + set timeout
        """
        msg = "{}[CONNECT] {}:{}:{}".format("[SKIP]" if self.isconn else "", self.hostname, self.host, self.port)
        self.dbg_print(msg)

        # Check connection - is NOT connected
        if not self.isconn:
            # Initiate connect
            self.__connect(timeout)

            # Get server prompt with retry
            for cnt in range(0, retry):
                try:
                    if self.__get_prompt():
                        break
                except Exception as e:
                    self.dbg_print("\t\t[RECONN] Wait for prompt [{}/{}]: {}".format(cnt+1, retry, e))
                    if "Busy server" in str(e):
                        self.__connect(timeout)
                # Wait between retries
                time.sleep(0.3)
            else:
                # Handle busy server connection case
                raise Exception("[EXIT] Server is busy, try later.")
        # Set hostname if empty to "short" prompt (prompt without " $")
        self.hostname = self.prompt.split()[0] if self.hostname is None else self.hostname
        # Auth connection
        self.__auth()
        return self.prompt

    def __auth(self):
        # Autofill password
        if self.password is not None and 'password' in self.preprompt:
            self.send_cmd(self.password, timeout=4)

    def __get_prompt(self, timeout=3):
        """Get and save prompt
        - return get prompt state (True/False)
        """
        self.dbg_print("[GET PROMPT]")
        if select.select([self.conn], [], [], timeout)[0]:
            prompt = self.conn.recv(256).decode('utf-8')        #.strip()
            # Special use-cases
            if 'Bye!' in prompt and "busy" in prompt:
                raise Exception("Busy server: {}".format(prompt))
            # Prompt use-case
            if '$' in prompt:
                # simple: prompt $
                # modes: [preprompt] prompt $
                self.prompt = ' '.join(prompt.split()[-2:])
                self.__filter_preprompt(prompt)
        self.dbg_print("\t|-> {}{}".format(f"{self.preprompt} ", self.prompt))
        return False if self.prompt is None else True

    def __filter_preprompt(self, _data):
        if len(_data) == 0:
            return
        last_line = _data.strip().split('\n')[-1]
        # get pre-prompt: >[configure]< prompt $
        if self.prompt is not None:
            # Check prompt is in last line
            if self.prompt in last_line:
                # Check pre-prompt - remove prompt
                x = last_line.replace(self.prompt, '')
                # SET preprompt if preprompt exists
                self.preprompt = x if len(x) > 0 else self.preprompt
            # Pre-prompt remove and cancel preprompt modes
            if self.preprompt in last_line:
                _data = _data.replace(self.preprompt, "")
            else:
                self.preprompt = ""
        return _data

    def __receive_data(self, read_timeout=20):
        """
        Client Receiver Loop
        - read_timeout - wait for server to reply (should be <15, avoid msg queue-ing)
        - managed by prompt (means server waiting for input)
        - Bye! - command closes the shell
        Output: data line list
        """

        data_buffer = ""
        # Collect answer data
        if select.select([self.conn], [], [], read_timeout)[0]:
            while True:
                data_buffer += self.conn.recv(4096).decode('utf-8')
                # Last line from data_buffer (handle fragmented messages - prompt detection)
                last_line = data_buffer.strip().split("\n")[-1]
                # Wait for prompt or special cases (exit/prompt)
                if "Bye!" in last_line:
                    self.dbg_print("\t\t[Bye!] Stop receiver loop")
                    break
                if self.prompt in last_line:
                    self.dbg_print("\t\t[{}] Stop receiver loop".format(self.prompt))
                    break
            self.dbg_print("\n\t\tData: {}".format(data_buffer))
            # Remove preprompt from last line if we have
            data_buffer = self.__filter_preprompt(data_buffer)
            # Remove prompt from output - only for msg end detection
            data_buffer = data_buffer.replace(self.prompt, '').rstrip()
            # Create list data output
            data_buffer = [k for k in data_buffer.split('\n') if k != '']
        return data_buffer

    def close(self):
        if self.conn is None:
            return
        self.dbg_print("[CLOSE] {}:{}:{}".format(self.hostname, self.host, self.port))
        self.conn.close()
        self.isconn = False
        self.spacer = 0

    def __run_command(self, cmd):
        """
        Run command on server tcp/ip connection
        - prompt check - validate device ("hostname $" = "prompt")
        - send command str
        - return reply line list / None (host miss-match)
        """
        reboot_request = True if 'reboot' in cmd.strip() else False
        cmd = str.encode(cmd)
        # Compare prompt |node01 $| with hostname 'node01.local'
        check_prompt = str(self.prompt).replace('$', '').strip()
        check_hostname = str(self.hostname).split('.')[0]
        if self.hostname is None or check_prompt == check_hostname:
            # Sun command on validated device
            self.conn.send(cmd)
            # Workaround for reboot command - micrOS async server cannot send Bye! msg before reboot.
            if reboot_request:
                return 'Bye!'
            data = self.__receive_data()
            return data
        # Skip command run: prompt and host not the same!
        print(f"[micrOSClient] {color.ERR}prompt mismatch{color.NC}, hostname: {check_hostname} prompt: {check_prompt} ")
        # Check UID?
        return None

    def send_cmd(self, cmd, timeout=3, retry=5):
        """
        Send command function - main usage for non interactive mode
        """

        start_time = time.time()

        # Check cmd is not empty
        if len(cmd.strip()) == 0:
            return None

        self.dbg_print("[⏰] Send: {} -> {}:{}:{}".format(cmd, self.hostname, self.host, self.port))
        # [SINGLE COMMAND CMD] Automatic connection handling - for single sessions
        if not self.isconn:
            self.dbg_print("Auto init connection (isconn:{})".format(self.isconn))
            self.connect(timeout=timeout, retry=retry)

        # @ Run command
        try:
            out = self.__run_command(cmd)
        except Exception as e:
            self.dbg_print("{}[ERR]{} send_cmd error: {}".format(color.ERR, color.NC, e))
            self.dbg_print("Auto deinit connection")
            self.close()
            out = None

        # Collect communication metrics
        delta_time = (time.time() - start_time)
        self.avg_reply[0] += delta_time
        self.avg_reply[1] += 1
        f_delta_t = "{}[{:.2f}]{}".format(color.OKGREEN, delta_time, color.NC)
        self.dbg_print("{}[⏰] {} {}reply: {}{}".format(f_delta_t, cmd, color.BOLD, out, color.NC))

        # return output list
        return out

    def send_cmd_retry(self, cmd, timeout=6, retry=5):
        out = None
        for cnt in range(0, retry):
            try:
                out = self.send_cmd(cmd, timeout)
                if out is None or isinstance(out, list):
                    break
            except OSError as e:
                    self.dbg_print("Host is down, timed out: {} sec e: {}".format(timeout, e))
                    break
            except Exception as e:
                if "Bye!" in str(e):
                    self.dbg_print("[Count] Send retry: {}/{}".format(cnt+1, retry))
            time.sleep(0.2)
        return out

    def telnet(self, timeout=4):
        """
        Implements interactive mode for socket communication.
        """
        try:
            self.connect(timeout)
        except Exception as e:
            print("Telnet connect: {}".format(e))
            if "busy" in str(e) or "timed out" in str(e) or "No route to host" in str(e) or "Host is down" in str(e):
                return
        while True:
            cmd = input("{}{} ".format(self.preprompt, self.prompt))
            # send command
            output = self.send_cmd(cmd)
            # Format output to human readable
            output = '\n'.join(output) if isinstance(output, list) else output
            # output to STDOUT
            if not (cmd.strip() == '' and output is None):
                print(output)
            # Close session
            if 'Bye!' in str(output):
                break
        self.close()

    def dbg_print(self, msg, end='\n'):
        if self.dbg:
            print(f"{color.HEADER}{' '*self.spacer}[dbg]{color.NC} {msg}", end=end)
            if self.spacer < 60:
                self.spacer += 1

    def load_test(self, timeout=3, cnt=10):
        load_test_simple = f"[CONN TEST] SEND HELLO x{cnt}\n\tDescription: Single connection testing - without " \
                           f"waiting prompt - load test "
        verdict = [load_test_simple]
        self.connect(timeout=timeout)
        cmd = str.encode("hello")
        delta_t_all = 0
        for k in range(0, cnt):
            start = time.time()
            print("\t[{}/{}] Send hello - load test".format(k+1, cnt))
            self.conn.send(cmd)
            data = self.__receive_data()
            delta_t = time.time() - start
            delta_t_all += delta_t
            console_msg = "[{}s] send hello, reply: {}".format(round(delta_t, 4), data)
            verdict.append(console_msg)
            print(f"===>\t\t{console_msg}")
        self.close()
        verdict.append(f"SINGLE CONNECTION LOAD TEST X{cnt}, AVERAGE REPLY TIME: {round(delta_t_all/cnt, 3)} sec\n")
        return verdict

    def __del__(self):
        if self.dbg and self.avg_reply[1] > 0:
            print(f"Response time: {round(self.avg_reply[0]/self.avg_reply[1], 2)} sec with {self.hostname}:{self.host}")
        self.close()


def micros_connection_metrics(address):

    def multi_conn_load(addr, cnt=10):
        all_reply = []
        _all_delta_t = 0
        _success = 0
        for count in range(0, cnt):
            start = time.time()
            con_obj = micrOSClient(host=addr, port=9008, pwd="ADmin123", dbg=True)
            try:
                reply_msg = '\n'.join(con_obj.send_cmd("hello", retry=1))
                _success += 1
            except Exception as e:
                reply_msg = str(e)
            con_obj.close()
            delta_t = time.time() - start
            _all_delta_t += delta_t
            _console_msg = f"[{round(delta_t, 4)}s] hello: {reply_msg}"
            print(f"\t\t{_console_msg}")
            all_reply.append(_console_msg)
        success_rate = int(round(_success / cnt, 2) * 100)
        all_reply.append(f"MULTI CONNECTION LOAD TEST X{cnt}, AVERAGE REPLY TIME: {round(_all_delta_t/cnt, 3)}s, "
                         f"SERVER AVAILABILITY: {success_rate}% ({round(_all_delta_t/_success, 3)}s)")
        return all_reply

    # ---------------------------------------------------- #
    high_level_verdict = []

    # [1] Create micrOSClient object + Run LOAD tests
    com_obj = micrOSClient(host=address, port=9008, pwd="ADmin123", dbg=True)
    # [1.1] Run load test in one connection
    verdict_list = com_obj.load_test()
    com_obj.close()
    high_level_verdict.append(verdict_list[-1])

    # [2] Run multi connection load test - reconnect - raw connection (without retry)
    verdict_multi = multi_conn_load(address)
    high_level_verdict.append((verdict_multi[-1]))

    ############################################################################
    print("=== TEST VERDICT ==="*20)
    print(f"{color.WARN} #### Single connection Load test (TCP){color.NC}")
    for k in verdict_list:
        print(f"\t{k}")
    print(f"{color.WARN} #### Multi connection Load test (TCP) - reconnect measurement{color.NC}")
    for k in verdict_multi:
        print(f"\t{k}")

    return high_level_verdict


if __name__ == "__main__":
    force_close = True

    address = 'TinyDevBoard.local'
    #address = '192.168.1.239'
    #address = '192.168.1.91'

    # [1] Create micrOSClient object
    com_obj = micrOSClient(host=address, port=9008, pwd="ADmin123", dbg=True)

    # [2] Test functions for command send function
    print(f"{color.WARN}[1] #### Write hello{color.NC}")
    hello = com_obj.send_cmd_retry("hello")
    print("hello: {}".format(hello))
    if force_close: com_obj.close()


    print(f"{color.WARN}[2] #### Write version{color.NC}")
    version = com_obj.send_cmd_retry("version")
    print("version: {}".format(version))
    if force_close: com_obj.close()

    print(f"{color.WARN}[3] #### Conf - single connection{color.NC}")
    conf_mode = com_obj.send_cmd_retry("conf")
    dbg_value = com_obj.send_cmd_retry("dbg")
    noconf_mode = com_obj.send_cmd_retry("noconf")
    print("dbg: {}".format(dbg_value))
    print(f"conf out: {conf_mode}")
    print(f"noconf out: {noconf_mode}")
    if force_close: com_obj.close()

    verdict = micros_connection_metrics(address=address)
    for k in verdict:
        print(f"+\t\t{k}")

    # [3] Start interactive mode
    print(f"{color.WARN}[5] #### Start micrOS telnet{color.NC}")
    com_obj.telnet()
