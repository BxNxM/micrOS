# https://www.geeksforgeeks.org/python-build-a-rest-api-using-flask/
# https://stackoverflow.com/questions/48095713/accepting-multiple-parameters-in-flask-restful-add-resource
# using flask_restful
import json
import os
from flask import Flask, jsonify, Response, make_response, request, send_file, abort
from flask_restful import Resource, Api
import threading
import time
import concurrent.futures
MYPATH = os.path.dirname(__file__)
import requests
from io import BytesIO
from socket import gethostbyname

try:
    from flask_basicauth import BasicAuth
    from datetime import datetime
except Exception as e:
    print("[GW-AUTH] Cannot load flask_basicauth->BasicAuth")
    BasicAuth = None

try:
    from . import socketClient
    from .lib.SearchDevices import my_local_ip
    from .lib.LocalMachine import CommandHandler, FileHandler
except Exception as e:
    print("Import warning __name__:{}: {}".format(__name__, e))
    import socketClient
    from lib.SearchDevices import my_local_ip
    from lib.LocalMachine import CommandHandler, FileHandler

API_URL_CACHE = ""

# creating the flask app
app = Flask(__name__)

# --------------------- AUTH BEGIN ------------------------- #
ADDRESS_CACHE = {}
try:
    print("[GW-AUTH][HINT] API_AUTH=usr:pwd:optional\toptional country codes: HU,GB,CA")
    __conf = tuple(os.environ.get("API_AUTH").split(':'))
    if len(__conf) == 2:
        __rest_usr_name, __rest_usr_pwd = __conf
        ALLOWED_COUNTRY = []
        print("[GW-AUTH][ENABLED] NO WHITELISTED COUNTRIES (CURRENT ONLY - FALLBACK)")
    else:
        __rest_usr_name, __rest_usr_pwd, ALLOWED_COUNTRY = __conf
        ALLOWED_COUNTRY = [c.strip() for c in ALLOWED_COUNTRY.split(',')]
        print(f"[GW-AUTH][ENABLED] {ALLOWED_COUNTRY}")
except Exception as e:
    print("[GW-AUTH][DISABLED] API_AUTH ENV VAR NOT FOUND.")
    __rest_usr_name, __rest_usr_pwd, ALLOWED_COUNTRY = None, None, []


if BasicAuth is not None and (__rest_usr_name and __rest_usr_pwd):
    basic_auth = BasicAuth(app)

    # Configure basic authentication
    app.config['BASIC_AUTH_USERNAME'] = f'{__rest_usr_name}'
    app.config['BASIC_AUTH_PASSWORD'] = f'{__rest_usr_pwd}'
    #app.config['BASIC_AUTH_PASSWORD'] = f'{__rest_usr_pwd}{datetime.now().day}'  # month-day (21)

    def _is_local_network():
        # Define local network IP prefixes (adjust as needed)
        local_network_prefixes = ['192.168.', '10.0.', '172.']
        #local_network_prefixes = []
        remote_ip = request.remote_addr
        print(f"\t[GW-AUTH] Check incoming IP address: {remote_ip}")
        for prefix in local_network_prefixes:
            if remote_ip.startswith(prefix):
                print(f"\t\t[GW-AUTH] SKIP AUTH - LOCAL NETWORK: {prefix} match with {remote_ip}")
                return True, remote_ip
        return False, remote_ip


    def allow_gateway_country():
        global ALLOWED_COUNTRY
        try:
            response = requests.get('https://httpbin.org/ip')
            gateway_extip = response.json()['origin']
            print(f"[!][GW-AUTH][!] gw ext ip: {gateway_extip}")
        except Exception as e:
            print(f"[!][GW-AUTH][!] gateway_country error: {e}")
            return None
        _, location = _location_filter(gateway_extip)
        if location['ok']:
            ALLOWED_COUNTRY.append(location['Country'])
            print(f"[!][GW-AUTH][!] extend ALLOWED_COUNTRY with {ALLOWED_COUNTRY}")


    def _location_filter(ip_address):
        enabled_country_codes = ALLOWED_COUNTRY
        if ADDRESS_CACHE.get(ip_address) is None:
            api_url = f'http://ipinfo.io/{ip_address}/json'
            try:
                data = requests.get(api_url).json()
                # Extract relevant location information
                country = data.get('country', 'N/A')
                city = data.get('city', 'N/A')
                region = data.get('region', 'N/A')
                response = {"ok": True, "Country": country, "Region": region, "City": city}
            except Exception as e:
                response = {"ok": False, "Country": str(e)}
            if response["ok"] and response["Country"] in enabled_country_codes:
                print(f"\t[GW-AUTH] EXTERNAL LOGIN: ALLOW ({enabled_country_codes}) EXTERNAL IP ({ip_address}) FROM: {response}")
                ADDRESS_CACHE[ip_address] = (True, response)
                return True, response
            print(f"\t[GW-AUTH] EXTERNAL LOGIN: DENY - EXTERNAL IP ({ip_address}) FROM: {response}")
            ADDRESS_CACHE[ip_address] = (False, response)
            return False, response
        # Return cached value:
        print(f"\t[GW-AUTH] CACHE::: {ADDRESS_CACHE}")
        return ADDRESS_CACHE[ip_address]


    @app.before_request
    def require_authentication():
        is_internal, remote_ip = _is_local_network()
        print(f"[GW-AUTH] {'INTERNAL' if is_internal else 'EXTERNAL'} LOGIN: {remote_ip}")
        if not is_internal and not basic_auth.authenticate():
            if len(ALLOWED_COUNTRY) == 0:
                allow_gateway_country()
            allowed, _ = _location_filter(remote_ip)
            if allowed:
                return basic_auth.challenge()
            return abort(401)
# ------------------------------------ AUTH END -------------------------------------- #

# creating an API object
api = Api(app)


##################################################################
##                       ENDPOINT DEFINITIONS                   ##
##################################################################


class Hello(Resource):
    # corresponds to the GET request.
    # this function is called whenever there
    # is a GET request for this resource

    def get(self):
        index_html = os.path.join(MYPATH, 'index.html')
        try:
            with open(index_html, 'r') as file:
                html = file.read()
            response = html
        except OSError:
            response = "404 Not Found"
        return make_response(response)


class SendCmd(Resource):
    """
    http://127.0.0.1:5000/sendcmd/micr240ac4f679e8OS/rgb+toggle
        {
          "cmd": [
            "rgb",
            "toggle"
          ],
          "device": [
            "micr240ac4f679e8OS",
            "192.168.1.91",
            9008,
            "Chillight"
          ],
          "latency": 2.35,
          "response": [
            "B: 35",
            "S: 1",
            "G: 140",
            "R: 4"
          ]
        }
    """

    def get(self, device, cmd):
        return jsonify(self.runcmd(device, cmd))

    @staticmethod
    def runcmd(device, cmd):
        cmd_list = cmd.split('+')
        cmd_str = ' '.join(cmd_list)

        ip, port, fid, uid = socketClient.ConnectionData.select_device(device_tag=device)
        device_detailed = (uid, ip, port, fid)

        print("[Gateway] Raw command params: --dev {} {}".format(uid, cmd_str))
        start = time.time()
        status, response = socketClient.run(['--dev', uid, cmd_str])
        if status is False:
            # 1x retry (in the background, maybe the IP was refreshed)
            status, response = socketClient.run(['--dev', uid, cmd_str])
        diff = round(time.time() - start, 2)
        if cmd_str.strip() == 'help':
            # DO not format (strip) response
            if response is not None:
                response = response.splitlines() if '\n' in response else response.strip()
        else:
            # FORMAT (strip) response
            if response is not None:
                response = [k.strip() for k in response.splitlines()] if '\n' in response else response.strip()
        return {'cmd': cmd_list, 'device': device_detailed, 'response': response, 'latency': diff}

class ListDevices(Resource):
    DEVICE_CACHE = {}
    _THREAD_OBJ = None
    _LAST_EXEC_TIME = time.time()

    def sort_devices(self):
        device_struct = socketClient.ConnectionData.list_devices()
        online_devices = socketClient.ConnectionData.nodes_status()
        filtered_devices = {"online": {}, "offline": {}}
        for uid, data in device_struct.items():
            if data[0] in online_devices:
                filtered_devices['online'][uid] = data
            else:
                filtered_devices['offline'][uid] = data
        ListDevices.DEVICE_CACHE = filtered_devices
        ListDevices._LAST_EXEC_TIME = time.time()
        return filtered_devices

    def get(self):
        status = 'Done'
        filtered_devices = ListDevices.DEVICE_CACHE
        if len(ListDevices.DEVICE_CACHE) == 0:
            # No cache available - run without thread -> wait for result
            filtered_devices = self.sort_devices()
        elif ListDevices._THREAD_OBJ is None or (ListDevices._THREAD_OBJ and not ListDevices._THREAD_OBJ.is_alive()):
            # Cache is available refresh in the background
            ListDevices._THREAD_OBJ = threading.Thread(target=self.sort_devices, args=())
            ListDevices._THREAD_OBJ.start()
            status = 'start'
        elif ListDevices._THREAD_OBJ is not None and ListDevices._THREAD_OBJ.is_alive():
            # Cache is available refresh thread is already running
            status = 'running'
        else:
            # Thread finished - delete object - set state done
            ListDevices._THREAD_OBJ = None
            status = 'done'

        gateway_metrics = {'status': status, 'last[sec]': round(time.time()-ListDevices._LAST_EXEC_TIME, 1)}
        filtered_devices['gateway_metrics'] = gateway_metrics
        return jsonify(filtered_devices)


class SearchDevices(Resource):
    SEARCH_LIMIT_SEC = 30
    _THREAD_OBJ = None
    _LAST_EXEC_TIME = time.time()

    def _thread_worker(self):
        socketClient.ConnectionData.search_micrOS_on_wlan()
        SearchDevices._LAST_EXEC_TIME = time.time()

    def get(self):
        status = "Done"
        if SearchDevices._THREAD_OBJ:
            if SearchDevices._THREAD_OBJ.is_alive():
                status = "Running"
            else:
                status = "Done"
                SearchDevices._THREAD_OBJ = None
        else:
            delta_t = time.time() - SearchDevices._LAST_EXEC_TIME
            if delta_t > SearchDevices.SEARCH_LIMIT_SEC and SearchDevices._THREAD_OBJ is None:
                SearchDevices._THREAD_OBJ = threading.Thread(target=self._thread_worker, args=())
                SearchDevices._THREAD_OBJ.start()
                status = "Start"

        device_struct = socketClient.ConnectionData.list_devices()
        delta_t = time.time() - SearchDevices._LAST_EXEC_TIME
        gateway_metrics = {'status': status, 'last[sec]': round(delta_t, 1),
                           'qlimit[sec]': SearchDevices.SEARCH_LIMIT_SEC}
        return jsonify({'devices': device_struct, 'gateway_metrics': gateway_metrics})


class DeviceStatus(Resource):
    CLEAN_MICROS_ALARMS = True
    STATUS_LIMIT_SEC = 60
    NODE_STATUS = {}
    _THREAD_OBJ = None
    _LAST_EXEC_TIME = time.time()
    DEVS_AVAIL = 0

    def __get_node_status(self, device_struct, uid):
        devip = device_struct[uid][0]
        fuid = device_struct[uid][2]
        if fuid.startswith('__') and fuid.endswith('__'):
            return None
        status, version = socketClient.run(['--dev', fuid.strip(), 'version'])
        hwuid = uid
        alarms = 'Unknown'
        upython_version = 'Unknown'
        free_ram = 'Unknown'
        free_fs = 'Unknown'
        cpu_temp = 'Unknown'
        diff = 0

        if status:
            start = time.time()

            # Get hello message response
            _status, hello = socketClient.run(['--dev', fuid.strip(), 'hello'])
            diff = round(time.time() - start, 2)
            if _status:
                try:
                    hwuid = hello.strip().split(':')[2]
                except:
                    hwuid = uid

            # Get system alarms response
            _status2, alarms = socketClient.run(['--dev', fuid.strip(), 'system alarms'])
            if _status2:
                alarms = alarms.splitlines()
                try:
                    alarms = {'verdict': alarms[-1], 'log': alarms[0:-1]}
                except:
                    alarms = {'verdict': "NOK", "log": []}

            # Clean Alarms
            clean_alarms = DeviceStatus.CLEAN_MICROS_ALARMS
            log_data = alarms.get('log', None)
            if clean_alarms and log_data and len(log_data) > 0:
                _, _ = socketClient.run(['--dev', fuid.strip(), 'system alarms True'])

            # Get system info response -> upython version
            _status3, info = socketClient.run(['--dev', fuid.strip(), 'system info >json'])
            if _status3:
                try:
                    info = json.loads(info)
                    print(info)
                    free_ram = 100 - info.get('Mem usage [%]')
                    free_fs = 100 - info.get('FS usage [%]')
                    upython_version = info.get('upython')
                except Exception as e:
                    print(f"System info query error: {e}")
                    pass

            # Get cpu temp
            _status4, cpu_temp = socketClient.run(['--dev', fuid.strip(), 'esp32 temp'])
            if 'temp' in cpu_temp:
                try:
                    cpu_temp = cpu_temp.split(":")[1].strip()
                except:
                    pass
        return hwuid, status, fuid, devip, version, alarms, diff, upython_version, cpu_temp, free_fs, free_ram

    def get_all_node_status(self):
        output_dev_struct = {}
        online_dev_cnt = 0
        device_struct = socketClient.ConnectionData.list_devices()
        dev_query_list = []

        # Start parallel status queries
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for uid in device_struct.keys():
                future = executor.submit(self.__get_node_status, device_struct, uid)
                dev_query_list.append(future)

        # Collect results from queries
        for query in dev_query_list:
            node_info = query.result()

            if node_info is None:
                continue
            # Unwrap data
            hwuid, status, fuid, devip, version, alarms, diff, upython_version, cpu_temp, free_fs, free_ram = node_info

            # Status calculation
            if status:
                online_dev_cnt += 1
                DeviceStatus.DEVS_AVAIL = round((online_dev_cnt / (len(device_struct)-2)) *100, 1)
                status = 'HEALTHY'
            else:
                status = 'UNHEALTHY'

            output_dev_struct[hwuid] = {'verdict': status, 'fuid': fuid,
                                        'devip': devip, "version": version,
                                        'alarms': alarms, "latency": diff,
                                        'upython': upython_version, 'cpu_temp': cpu_temp,
                                        'free_fs': free_fs, 'free_ram': free_ram}

        DeviceStatus.NODE_STATUS = output_dev_struct
        DeviceStatus._LAST_EXEC_TIME = time.time()
        return output_dev_struct

    def get(self):
        status = "Done"
        if DeviceStatus._THREAD_OBJ:
            if DeviceStatus._THREAD_OBJ.is_alive():
                status = "Running"
            else:
                status = "Done"
                DeviceStatus._THREAD_OBJ = None
        else:
            delta_t = time.time() - DeviceStatus._LAST_EXEC_TIME
            if delta_t > DeviceStatus.STATUS_LIMIT_SEC or len(DeviceStatus.NODE_STATUS.keys()) <= 0:
                DeviceStatus._THREAD_OBJ = threading.Thread(target=self.get_all_node_status, args=())
                DeviceStatus._THREAD_OBJ.start()
                status = "Start"

        delta_t = time.time() - DeviceStatus._LAST_EXEC_TIME
        gateway_metrics = {'status': status, 'last[sec]': round(delta_t, 1),
                           'device_count': len(socketClient.ConnectionData.list_devices().keys())-2,
                           'availablity[%]': DeviceStatus.DEVS_AVAIL, 'qlimit[sec]': DeviceStatus.STATUS_LIMIT_SEC}
        return jsonify({'devices': DeviceStatus.NODE_STATUS,
                        'gateway_metrics': gateway_metrics})


class Prometheus(Resource):

    # corresponds to the GET request.
    # this function is called whenever there
    # is a GET request for this resource

    def list_string_to_dict_hack(self, list_resp):
        special_chars = ['%', '&', '-', '[', ']', '{', '}', ':']
        output_dict = {}
        for line in list_resp:
            _var = ""
            _val = ""
            for ch in line:
                if ch.isdigit() or '.' == ch:
                    _val += ch
                elif ch not in special_chars:
                    _var += ch
            _var = _var.strip().replace(' ', '_')
            try:
                output_dict[_var] = float(_val)
            except Exception as e:
                print(f"Invalid value to float {_var} == {_val}: {e}")
        if len(output_dict.keys()) == 0:
            output_dict = {'Unknown': -1}       # Error value -1
        return output_dict

    def response_converter(self, response, tag):
        """
        Convert micrOS cmd execution response to prometheus format
        """
        # Hack out special key characters
        response = response.replace('[', '').replace(']', '').replace('%', '')

        response_out = []
        try:
            # Normally expected dict (json) format as cmd output
            response = json.loads(response)
        except Exception as e:
            print(f"Prometheus response_converter non json error: {e}\n->Response:\n{response}")
            try:
                # Handle multi line raw string as input
                response = self.list_string_to_dict_hack(response)
            except Exception as e:
                print(f"\tlist_string_to_dict_hack error: {e}")
                response = {'Unknown': -1}

        # Generate Prometheus reply based on micrOS REST API parsed response
        for resp_key in response.keys():
            value = response[resp_key]
            doc = f"Dynamic content: {resp_key}"
            c_tag = f"{tag}_{resp_key.split()[0]}"    # [custom tag] Add returned value key to tag to make it unique by response
            response_out.append(f"# TYPE python_info gauge\n# HELP {c_tag} {doc}\n# TYPE {c_tag} gauge\n{c_tag} {value}")
        response_out = '\n'.join(response_out).strip()
        print(f"Generate Prometheus (multi value) output:\n---\n{response_out}\n---")
        return response_out

    def eval_rest_response(self, output):
        """Convert json string / string to tag, value and description"""
        try:
            _board = output['device'][3]
        except Exception as e:
            print(f"Prometheus responder _board extract error: {e}")
            _board = None

        try:
            if len(output['cmd']) > 1:
                _cmd_short = '_'.join(output['cmd'][0:2])
            else:
                _cmd_short = output['cmd'][0]
            tag = f"micrOS_{_board}__{_cmd_short}"
            prometheus_response = self.response_converter(output['response'], tag)
        except Exception as e:
            print(f"Prometheus responder tag, description and value extract error: {e}")
            prometheus_response = -1
        return prometheus_response
    def get(self, device, cmd):
        if not cmd.endswith('>json'):
            # Add json formatting to cmd request (due to parsing)
            cmd = f"{cmd}+>json"
        output = self.execution(device, cmd)
        prometheus_response = self.eval_rest_response(output)
        return Response(prometheus_response, mimetype='text/plain')

    def execution(self, device, cmd):
        return SendCmd.runcmd(device, cmd)


class ForwardImg(Resource):
    """
    Image broadcaster endpoint
    - list camera modules
    - get picture from camera module
    """
    RESOLVED_URLS = {}
    CAM_DEVICES = set()

    @staticmethod
    def _host_cache(url):
        try:
            # Extracting the hostname from the URL
            hostname = url.split('/')[2]
            # Resolving the IP address
            ip_address = gethostbyname(hostname)
            resolved_url = url.replace(hostname, ip_address)
            ForwardImg.RESOLVED_URLS[url] = resolved_url
        except Exception as e:
            print(f"URL has no hostname: {url} - fallback to u resolved url: {e}")
            ForwardImg.RESOLVED_URLS[url] = url  # fallback
        return ForwardImg.RESOLVED_URLS[url]

    def _get_image(self, device):
        base_url = ForwardImg._host_cache(f"http://{device}.local")
        internal_image_url = f"{base_url}/cam/snapshot"
        # Make a request to the external image URL
        try:
            response = requests.get(internal_image_url, timeout=10)
            # Check if the request was successful
            if response.status_code == 200:
                # Get the content of the image
                image_content = response.content
                # Create a BytesIO object to send the image as a file-like object
                image_stream = BytesIO(image_content)
                # Auto update device pool - no need to search after one successful communication (incase sensitive check)
                if sum([1 for d in ForwardImg.CAM_DEVICES if d.lower() == device.lower()]) == 0:
                    ForwardImg.CAM_DEVICES.add(device)
                # Send the image as a response
                return send_file(image_stream, mimetype='image/jpeg')
            print(f"[ForwardImg] Image get wrong response (error): {response}")
        except Exception as e:
                print(f"[ForwardImg] Image get timeout (error): {e}")
        return None

    @staticmethod
    def find_cam_endpoints():
        if len(ListDevices.DEVICE_CACHE) == 0:
            ListDevices().get()

        if len(list(ForwardImg.CAM_DEVICES)) > 0:
            # skip refresh  - TODO start background task ?
            return jsonify(list(ForwardImg.CAM_DEVICES))

        for devid, dev_conn_data in ListDevices.DEVICE_CACHE['online'].items():
            # IP, PORT, FID
            device = dev_conn_data[2]
            response = SendCmd.runcmd(device, 'modules')['response']
            print(f"\n\n{response}\n\n")
            if 'OV2640' in response:
                ForwardImg.CAM_DEVICES.add(device)
        return jsonify(list(ForwardImg.CAM_DEVICES))

    def get(self, device=None):
        if device is None:
            return ForwardImg.find_cam_endpoints()
        img = self._get_image(device)
        if img is None:
            return "Failed to retrieve image from external endpoint", 500
        return img

class ImgStream(Resource):
    # corresponds to the GET request.
    # this function is called whenever there
    # is a GET request for this resource

    def get(self):
        index_html = os.path.join(MYPATH, 'img_stream.html')
        try:
            with open(index_html, 'r') as file:
                html = file.read()
            response = html
        except OSError:
            response = "404 Not Found"
        return make_response(response)

class WebHook(Resource):
    ACTION_SCRIPTS_PATH = os.path.join(MYPATH, 'user_data/webhooks')

    def get(self, payload=None, args=None):
        if payload is None:
            return self.webhook_help()
        response = {'exitcode': 1, 'response': ''}
        script = os.path.join(WebHook.ACTION_SCRIPTS_PATH, f"{payload}.py")
        if os.path.isfile(script):
            args = ' '.join(args.split('+')) if args is not None else ''
            cmd = f"python3 {script} {args}"
            response['exitcode'], response['response'], stderr = CommandHandler.run_command(cmd, raise_exception=True, shell=True, debug=True)
            print(f"[WEBHOOK][{response['exitcode']}{stderr}] {script} {args}")
        else:
            print(f"[WEBHOOK] no payload script was found: {script}")
        return jsonify(response)

    def webhook_help(self):
        webhook_scripts = FileHandler.list_dir(WebHook.ACTION_SCRIPTS_PATH)
        response = {'webhooks_folder': WebHook.ACTION_SCRIPTS_PATH, 'webhooks': webhook_scripts}
        return jsonify(response)



# adding the defined resources along with their corresponding urls
api.add_resource(Hello, '/')
api.add_resource(ListDevices, '/list/')
api.add_resource(SearchDevices, '/search/')
api.add_resource(DeviceStatus, '/status')
api.add_resource(SendCmd, '/sendcmd/<string:device>/<string:cmd>')
api.add_resource(Prometheus, '/metrics/<string:device>/<string:cmd>')
api.add_resource(ForwardImg, '/image', '/image/<string:device>')
api.add_resource(ImgStream, '/imgstream')
api.add_resource(WebHook, '/webhooks', '/webhooks/<string:payload>', '/webhooks/<string:payload>/<string:args>')


def gateway(debug=True):
    global API_URL_CACHE
    API_URL_CACHE = f"http://{my_local_ip()}:5000"
    print("\n############### START MICROS GATEWAY ###############")
    print("#             {}            #".format(API_URL_CACHE))
    print("####################################################\n")
    app.run(debug=debug, use_reloader=debug, host='0.0.0.0', port=5000)     # host='0.0.0.0' automatic, manual: host=my_local_ip()


# driver function
if __name__ == '__main__':
    gateway()
