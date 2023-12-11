# https://www.geeksforgeeks.org/python-build-a-rest-api-using-flask/
# https://stackoverflow.com/questions/48095713/accepting-multiple-parameters-in-flask-restful-add-resource
# using flask_restful
import json

from flask import Flask, jsonify, Response, make_response
from flask_restful import Resource, Api
import threading
import time
import concurrent.futures

try:
    from . import socketClient
    from .lib.SearchDevices import my_local_ip
except Exception as e:
    print("Import warning __name__:{}: {}".format(__name__, e))
    import socketClient
    from lib.SearchDevices import my_local_ip

API_URL_CACHE = ""

# creating the flask app
app = Flask(__name__)
# creating an API object
api = Api(app)

# making a class for a particular resource
# the get, post methods correspond to get and post requests
# they are automatically mapped by flask_restful.
# other methods include put, delete, etc.
class Hello(Resource):

    # corresponds to the GET request.
    # this function is called whenever there
    # is a GET request for this resource

    def built_in_html(self):
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <meta name="theme-color" media="(prefers-color-scheme: dark)" content="black" />
    <title>Flask Web Server</title>
    <style>
        @keyframes backgroundAnimation {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}}
        body {
            height: 100vh;
            padding: env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left);
            margin: 40px;
            background: linear-gradient(110deg, #4b3c66, #21184f, #712336);
            background-size: 400% 400%;
            animation: backgroundAnimation 15s infinite;
            color: #d9d9d9;
            font-family: 'Arial', sans-serif;
        }
    </style>
</head>
<body>
    <img src="https://github.com/BxNxM/micrOS/blob/master/media/logo_mini.png?raw=true" alt="micrOS Logo" width="60" height="60">
    <h1> micrOS GATEWAY </h1>
    <!-- Display SysApiCall output -->
    <p id="SysApiCall"></p>
    <p> micrOS gateway 'v1.1' </p>
    <p> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;/list &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; List known devices, sort by online/offline </p> 
    <p> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;/search &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Search devices </p> 
    <p> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;/status &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Get all device status - node info </p> 
    <p> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;/sendcmd/&lt;device&gt;/&lt;cmd&gt &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Send command to the selected device. Use + instead of space </p> 
    <p> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;/metrics/&lt;device&gt;/&lt;cmd&gt &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; REST API endpoint for Prometheus scraping, (prometheus format) </p> 

    <h2> 🚀REST API </h2>
    <p>Clickable examples 🕹</p>
    <button onclick="restApi('list')">Devices</button>
    <button onclick="restApi('status')">Status</button>

    <!-- Input field for string -->
    <label for="inputApiCmd"> <h3>⚙️ Enter micrOS command:</h3> </label>
    <input type="text" id="inputApiCmd">
    <!-- Button to send data -->
    <button onclick="restApi()">Send</button>
    <!-- Display usrApiCallUrl generated from inputApiCmd -->
    <p id="usrApiCallUrl"></p>
    <!-- Display api response -->
    <pre id="usrApiCallResponse"></pre>
    <!-- Display response time in ms -->
    <p id="rest_response_time"></p>

    <script>
        const currentHostname = window.location.hostname;

        function restApi(cmd = '') {
            let inputApiCmd = ''
            if (cmd == '') {inputApiCmd=document.getElementById('inputApiCmd').value;
            } else {inputApiCmd = cmd;}
            cmd = inputApiCmd.trim().replace(/\s+/g, '/');

            // Get the current hostname and create the REST API URL
            // const currentHostname = window.location.hostname;
            let apiUrl = `http://${currentHostname}:5000/${cmd}`;

            const startTime = performance.now();
            let endTime;

            // Call rest api with command parameter
            fetch(apiUrl).then(response => {
                // Check if the request was successful (status code 200)
                if (!response.ok) {throw new Error('Network response was not ok: '+response.status);}
                // Parse the JSON response
                endTime = performance.now();
                return response.json();
            }).then(data => {
                // Display the generated URL on the webpage
                document.getElementById('usrApiCallUrl').innerHTML=`<strong>Generated URL:</strong><br> <a href="${apiUrl}" target="_blank" style="color: white;">${apiUrl}</a>`;

                // Handle the data received from the server
                document.getElementById('usrApiCallResponse').innerHTML=JSON.stringify(data, null, 4).replace(/\\n/g, "<br/>"+"&nbsp;".repeat(15));
                const delta = (endTime - startTime).toFixed(0);
                document.getElementById('rest_response_time').innerHTML=`⏱ Response time: ${delta} ms`;

                // Update sys info
                if (cmd == '') {document.getElementById('SysApiCall').innerHTML=Object.entries(data['result'])
                                                     .map(([key, value])=>`${key}: ${JSON.stringify(value)}`)
                                                     .join('  ❖  ').replace(/"/g, '');}
            }).catch(error => {console.error('Fetch error:', error, data);});
        }
        // Init basic info from board
        restApi()
    </script>
</body>
</html> 
        """
        return html
    def get(self):
        return make_response(self.built_in_html())


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
            _status3, info = socketClient.run(['--dev', fuid.strip(), 'system info'])
            if 'upython' in info:
                try:
                    free_ram = info.splitlines()[1].split(":")[-1].strip()
                    free_fs = info.splitlines()[2].split(":")[-1].strip()
                    upython_version = info.splitlines()[3].split(":")[-1].strip()
                except:
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
                #print(f"{_var} == {_val}")
            except Exception as e:
                print(f"Invalid value to float {_var} == {_val}: {e}")
        if len(output_dict.keys()) == 0:
            output_dict = {'Unknown': -1}       # Error value -1
        return output_dict

    def response_converter(self, response, tag):
        """
        Convert micrOS cmd execution response to prometheus format
        """
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


# adding the defined resources along with their corresponding urls
api.add_resource(Hello, '/')
api.add_resource(ListDevices, '/list/')
api.add_resource(SearchDevices, '/search/')
api.add_resource(DeviceStatus, '/status')
api.add_resource(SendCmd, '/sendcmd/<string:device>/<string:cmd>')
api.add_resource(Prometheus, '/metrics/<string:device>/<string:cmd>')


def gateway():
    global API_URL_CACHE
    API_URL_CACHE = f"http://{my_local_ip()}:5000"
    print("\n############### START MICROS GATEWAY ###############")
    print("#             {}            #".format(API_URL_CACHE))
    print("####################################################\n")
    app.run(debug=True, host='0.0.0.0', port=5000)     # host='0.0.0.0' automatic, manual: host=my_local_ip()


# driver function
if __name__ == '__main__':
    gateway()
