# https://www.geeksforgeeks.org/python-build-a-rest-api-using-flask/
# https://stackoverflow.com/questions/48095713/accepting-multiple-parameters-in-flask-restful-add-resource
# using flask_restful
from flask import Flask, jsonify
from flask_restful import Resource, Api
import threading
import time
import socket
import concurrent.futures

try:
    from . import socketClient
except Exception as e:
    print("Import warning __name__:{}: {}".format(__name__, e))
    import socketClient

# creating the flask app
app = Flask(__name__)
# creating an API object
api = Api(app)


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    s.close()
    return local_ip


# making a class for a particular resource
# the get, post methods correspond to get and post requests
# they are automatically mapped by flask_restful.
# other methods include put, delete, etc.
class Hello(Resource):

    # corresponds to the GET request.
    # this function is called whenever there
    # is a GET request for this resource
    def get(self):
        manual = {'micrOS gateway': 'v0.3',
                  '/list': 'List known devices.',
                  '/search': 'Search devices',
                  '/status': 'Get all device status',
                  '/sendcmd/<device>/<cmd>': 'Send command to the selected device. Use + instead of space.'}
        return jsonify(manual)


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
        return jsonify({'cmd': cmd_list, 'device': device_detailed, 'response': response, 'latency': diff})


class ListDevices(Resource):

    def get(self):
        device_struct = socketClient.ConnectionData.list_devices()
        online_devices = socketClient.ConnectionData.nodes_status()
        filtered_devices = {"online": {}, "offline": {}}
        for uid, data in device_struct.items():
            if data[0] in online_devices:
                filtered_devices['online'][uid] = data
            else:
                filtered_devices['offline'][uid] = data
        return jsonify(filtered_devices)


class SearchDevices(Resource):
    SEARCH_LIMIT_SEC = 30
    _THREAD_OBJ = None
    _LAST_EXEC_TIME = time.time()
    _LAST_DELTA = 0

    def search_thread(self):
        SearchDevices._THREAD_OBJ = threading.Thread(target=socketClient.ConnectionData.search_micrOS_on_wlan, args=())
        SearchDevices._THREAD_OBJ.start()

    def get(self):
        status = "Done"
        if SearchDevices._THREAD_OBJ:
            if SearchDevices._THREAD_OBJ.is_alive():
                SearchDevices._LAST_DELTA = time.time() - SearchDevices._LAST_EXEC_TIME
                status = "Running"
            else:
                SearchDevices._LAST_DELTA = time.time() - SearchDevices._LAST_EXEC_TIME
                status = "Done"
                SearchDevices._THREAD_OBJ = None
                SearchDevices._LAST_EXEC_TIME = time.time()
        else:
            SearchDevices._LAST_DELTA = time.time() - SearchDevices._LAST_EXEC_TIME
            if SearchDevices._LAST_DELTA > SearchDevices.SEARCH_LIMIT_SEC:
                status = "Start"
                self.search_thread()

        device_struct = socketClient.ConnectionData.list_devices()
        gateway_metrics = {'status': status, 'last[sec]': round(SearchDevices._LAST_DELTA, 1),
                           'qlimit[sec]': SearchDevices.SEARCH_LIMIT_SEC}
        return jsonify({'devices': device_struct, 'gateway_metrics': gateway_metrics})


class DeviceStatus(Resource):
    CLEAN_MICROS_ALARMS = True
    STATUS_LIMIT_SEC = 60
    NODE_STATUS = {}
    _THREAD_OBJ = None
    _LAST_EXEC_TIME = time.time()
    _LAST_DELTA = 0
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
                    pass

            # Clean Alarms
            clean_alarms = DeviceStatus.CLEAN_MICROS_ALARMS
            if clean_alarms and 'NOK' in str(alarms):
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

    def status_thread(self):
        DeviceStatus._THREAD_OBJ = threading.Thread(target=self.get_all_node_status, args=())
        DeviceStatus._THREAD_OBJ.start()

    def get(self):
        status = "Done"
        if DeviceStatus._THREAD_OBJ:
            if DeviceStatus._THREAD_OBJ.is_alive():
                DeviceStatus._LAST_DELTA = time.time() - DeviceStatus._LAST_EXEC_TIME
                status = "Running"
            else:
                DeviceStatus._LAST_DELTA = time.time() - DeviceStatus._LAST_EXEC_TIME
                status = "Done"
                DeviceStatus._THREAD_OBJ = None
                DeviceStatus._LAST_EXEC_TIME = time.time()
        else:
            DeviceStatus._LAST_DELTA = time.time() - DeviceStatus._LAST_EXEC_TIME
            if DeviceStatus._LAST_DELTA > DeviceStatus.STATUS_LIMIT_SEC or len(DeviceStatus.NODE_STATUS.keys()) <= 0:
                status = "Start"
                self.status_thread()

        gateway_metrics = {'status': status, 'last[sec]': round(DeviceStatus._LAST_DELTA, 1),
                           'device_count': len(socketClient.ConnectionData.list_devices().keys())-2,
                           'availablity[%]': DeviceStatus.DEVS_AVAIL, 'qlimit[sec]': DeviceStatus.STATUS_LIMIT_SEC}
        return jsonify({'devices': DeviceStatus.NODE_STATUS,
                        'gateway_metrics': gateway_metrics})


# adding the defined resources along with their corresponding urls
api.add_resource(Hello, '/')
api.add_resource(ListDevices, '/list/')
api.add_resource(SearchDevices, '/search/')
api.add_resource(DeviceStatus, '/status')
api.add_resource(SendCmd, '/sendcmd/<string:device>/<string:cmd>')


def gateway():
    print("\n############### START MICROS GATEWAY ###############")
    print("#             http://{}:5000            #".format(get_local_ip()))
    print("####################################################\n")
    app.run(debug=True, host=get_local_ip(), port=5000)


# driver function
if __name__ == '__main__':
    gateway()
