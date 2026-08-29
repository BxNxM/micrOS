# https://www.geeksforgeeks.org/python-build-a-rest-api-using-flask/
# https://stackoverflow.com/questions/48095713/accepting-multiple-parameters-in-flask-restful-add-resource
# using flask_restful
import json
import os
import ipaddress
import ast
from html import escape
from urllib.parse import quote, unquote
from flask import Flask, jsonify, Response, make_response, request, send_file, send_from_directory, abort, stream_with_context
from flask_restful import Resource, Api
import threading
import time
import concurrent.futures
MYPATH = os.path.dirname(__file__)
WEBUI_PATH = os.path.join(MYPATH, 'gateway')
MICROS_WEBUI_PATH = os.path.join(os.path.dirname(MYPATH), 'micrOS', 'source', 'web')
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


@app.route('/gateway.css')
def gateway_css():
    return send_file(os.path.join(WEBUI_PATH, 'gateway.css'), mimetype='text/css')


@app.route('/micros-web/<path:resource>')
def micros_web_resource(resource):
    return send_from_directory(MICROS_WEBUI_PATH, resource)

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

if (__rest_usr_name and __rest_usr_pwd) and BasicAuth is None:
    raise RuntimeError("API_AUTH is configured, but flask_basicauth is not available")

if BasicAuth is not None and (__rest_usr_name and __rest_usr_pwd):
    basic_auth = BasicAuth(app)

    # Configure basic authentication
    app.config['BASIC_AUTH_USERNAME'] = f'{__rest_usr_name}'
    app.config['BASIC_AUTH_PASSWORD'] = f'{__rest_usr_pwd}'
    #app.config['BASIC_AUTH_PASSWORD'] = f'{__rest_usr_pwd}{datetime.now().day}'  # month-day (21)

    def _is_local_network():
        #local_network_prefixes = []
        remote_ip = request.remote_addr
        print(f"\t[GW-AUTH] Check incoming IP address: {remote_ip}")
        try:
            remote_addr = ipaddress.ip_address(remote_ip)
            if remote_addr.is_private or remote_addr.is_loopback:
                print(f"\t\t[GW-AUTH] SKIP AUTH - LOCAL NETWORK: {remote_ip}")
                return True, remote_ip
        except ValueError:
            print(f"\t\t[GW-AUTH] INVALID REMOTE IP: {remote_ip}")
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
        index_html = os.path.join(WEBUI_PATH, 'index.html')
        try:
            with open(index_html, 'r') as file:
                html = file.read()
            response = html
        except OSError:
            response = "404 Not Found"
        return make_response(response)


def _parse_dashboard_rest_cmd(cmd):
    """Mirror the device /rest path parsing for gateway dashboard calls."""
    decoded = unquote(cmd or '')
    tokens = []
    index = 0
    while index < len(decoded):
        if decoded[index] == '"':
            end = decoded.find('"', index + 1)
            if end == -1:
                tokens.append(decoded[index:].strip())
                break
            quoted_value = '"' + decoded[index + 1:end] + '"'
            if quoted_value:
                if tokens and tokens[-1].endswith('='):
                    tokens[-1] += quoted_value
                else:
                    tokens.append(quoted_value)
            index = end + 1
            continue

        start = index
        while index < len(decoded) and decoded[index] != '"':
            index += 1
        segment = decoded[start:index]
        if segment:
            segment = segment.replace('/', ' ').replace('-', ' ').strip()
            if segment:
                tokens.extend(token for token in segment.split() if token)
    return tokens


def _decode_dashboard_result(response):
    if response is None or isinstance(response, (dict, bool, int, float)):
        return response
    if isinstance(response, list):
        if len(response) != 1:
            return response
        response = response[0]
    text = str(response).strip()
    if not text:
        return text
    for loader in (json.loads, ast.literal_eval):
        try:
            return loader(text)
        except Exception:
            pass
    return response


def _dashboard_state(execution_result):
    response = execution_result.get('response')
    if isinstance(response, str) and response.startswith('Core error:'):
        return False
    return bool(execution_result.get('state', True))


def _gateway_auth_enabled():
    return bool(globals().get('__rest_usr_name') and globals().get('__rest_usr_pwd'))


class DeviceDashboardGroup(Resource):
    """
    One gateway page that groups every known device dashboard subpage.
    """

    @staticmethod
    def _device_groups():
        try:
            groups = ListDevices().sort_devices()
        except Exception as e:
            print(f"[GatewayDashboard] device group refresh error: {e}")
            groups = ListDevices.DEVICE_CACHE or {'online': {}, 'offline': {}}
        return {
            'online': {
                uid: data for uid, data in groups.get('online', {}).items()
                if len(data) > 2 and not str(data[2]).startswith('__')
            },
            'offline': {
                uid: data for uid, data in groups.get('offline', {}).items()
                if len(data) > 2 and not str(data[2]).startswith('__')
            }
        }

    @staticmethod
    def _device_tabs(label, devices, selected_device=''):
        if not devices:
            return '<div class="empty-row">No online devices available.</div>'
        links = []
        for uid, data in sorted(devices.items(), key=lambda item: str(item[1][2]).lower()):
            fuid = str(data[2])
            href = f"/dashboard/{quote(fuid, safe='')}"
            css_classes = ['device-tab']
            if fuid == selected_device:
                css_classes.append('active')
            title = escape(f"{fuid} ({uid})")
            links.append(
                f'<a class="{" ".join(css_classes)}" href="{href}" target="deviceFrame" '
                f'data-device="{escape(fuid)}" title="{title}">{escape(fuid)}</a>'
            )
        return f'<nav class="device-tabs" aria-label="{label}">' + ''.join(links) + '</nav>'

    def get(self):
        groups = self._device_groups()
        requested_device = request.args.get('device', '').strip()
        known_devices = {
            str(data[2]) for data in groups['online'].values()
        }
        first_online = next(iter(groups['online'].values()), None)
        first_device = requested_device if requested_device in known_devices else str(first_online[2]) if first_online else ''
        initial_src = f"/dashboard/{quote(first_device, safe='')}" if first_device else ''
        online_tabs = self._device_tabs('online devices', groups['online'], first_device)
        iframe = (
            f'<iframe name="deviceFrame" id="deviceFrame" src="{initial_src}" '
            'title="micrOS device dashboard"></iframe>'
            if initial_src else
            '<div class="empty-panel">No online device dashboard is available yet.</div>'
        )
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <meta name="theme-color" content="#101418">
    <title>micrOS Gateway Dashboards</title>
    <link rel="stylesheet" href="/gateway.css">
    <style>
        .dashboard-shell {{ min-height: 100vh; display: grid; grid-template-rows: auto 1fr; gap: 8px; padding: 10px; }}
        .dashboard-top {{ overflow: hidden; }}
        .device-tabs {{ display: flex; gap: 6px; overflow-x: auto; padding: 4px; }}
        .device-tab {{ display: inline-flex; align-items: center; justify-content: center; min-height: 30px; padding: 5px 10px; border-radius: 8px; background: var(--surface-strong); color: var(--text); text-decoration: none; font-weight: 700; font-size: 12px; white-space: nowrap; box-shadow: inset 0 0 0 1px var(--line); }}
        .device-tab.active {{ background: var(--accent); color: #101418; box-shadow: none; }}
        .dashboard-frame {{ min-height: calc(100vh - 56px); }}
        #deviceFrame {{ width: 100%; min-height: calc(100vh - 56px); border: 1px solid var(--line); border-radius: 8px; background: #000; }}
        .empty-row, .empty-panel {{ color: var(--muted); padding: 12px; border: 1px solid var(--line); border-radius: 8px; }}
        @media (max-width: 820px) {{
            .dashboard-shell {{ padding: 6px; }}
            #deviceFrame {{ min-height: calc(100vh - 48px); }}
        }}
    </style>
</head>
<body class="page-gateway">
    <main class="dashboard-shell">
        <section class="dashboard-top">
            {online_tabs}
        </section>
        <section class="dashboard-frame">
            {iframe}
        </section>
    </main>
    <script>
        document.querySelectorAll('.device-tab').forEach(link => {{
            link.addEventListener('click', () => {{
                document.querySelectorAll('.device-tab').forEach(item => item.classList.remove('active'));
                link.classList.add('active');
            }});
        }});
    </script>
</body>
</html>"""
        return make_response(html)


class DeviceDashboard(Resource):
    """
    Gateway-served micrOS dashboard.

    The HTML is loaded from micrOS/source/web/dashboard.html and only receives a
    device-scoped BASE_URL so the original dashboard code calls the gateway.
    """

    def get(self, device):
        dashboard_html = os.path.join(MICROS_WEBUI_PATH, 'dashboard.html')
        try:
            with open(dashboard_html, 'r', encoding='utf-8') as file:
                html = file.read()
        except OSError:
            abort(404, description=f"micrOS dashboard resource not found: {dashboard_html}")

        safe_device = escape(device)
        rest_base = f"/dashboard/{quote(device, safe='')}"
        html = html.replace(
            '<head>',
            '<head>\n    <base href="/micros-web/">',
            1
        )
        html = html.replace(
            '<title>Dashboard</title>',
            f'<title>micrOS Gateway Dashboard - {safe_device}</title>',
            1
        )
        html = html.replace(
            '<script src="uapi.js" ></script>',
            '<script src="uapi.js" ></script>\n'
            f'    <script>BASE_URL = {json.dumps(rest_base)};</script>',
            1
        )
        html = html.replace(
            '<h1> micrOS dashboard </h1>',
            f'<h1> micrOS dashboard - {safe_device}</h1>',
            1
        )
        return make_response(html)


class DeviceDashboardRest(Resource):
    """
    Device REST-compatible endpoint backed by gateway socket commands.
    """

    @staticmethod
    def device_info(device):
        _, _, fid, uid = socketClient.ConnectionData.select_device(device_tag=device)
        if uid is None:
            abort(404, description=f"Unknown device: {device}")
        version_call = SendCmd.runcmd(device, 'version')
        version = version_call.get('response') or 'Unknown'
        return jsonify({
            'result': {
                'micrOS': version,
                'node': fid,
                'auth': _gateway_auth_enabled(),
                'usr_endpoints': ('dashboard',)
            },
            'state': _dashboard_state(version_call)
        })

    def get(self, device, cmd=''):
        cmd_tokens = _parse_dashboard_rest_cmd(cmd)
        if not cmd_tokens:
            return self.device_info(device)

        if cmd_tokens[-1] != '>json':
            cmd_tokens.append('>json')
        execution = SendCmd.runcmd(device, '+'.join(cmd_tokens))
        return jsonify({
            'result': _decode_dashboard_result(execution.get('response')),
            'state': _dashboard_state(execution),
            'gateway': {
                'cmd': execution.get('cmd'),
                'device': execution.get('device'),
                'latency': execution.get('latency')
            }
        })


class DeviceDashboardEndpoint(Resource):
    """
    Gateway proxy for device web callbacks used by dashboard embed widgets.
    """
    ALLOWED_ENDPOINTS = ('cam/snapshot', 'cam/stream')

    def get(self, device, endpoint):
        endpoint = endpoint.strip('/')
        if endpoint not in self.ALLOWED_ENDPOINTS:
            abort(404, description=f"Unsupported dashboard endpoint: {endpoint}")

        ip, _, _, uid = socketClient.ConnectionData.select_device(device_tag=device)
        if uid is None:
            abort(404, description=f"Unknown device: {device}")
        device_url = f"http://{ip}/{endpoint}"
        try:
            upstream = requests.get(device_url, timeout=10, stream=True)
        except Exception as e:
            print(f"[GatewayDashboard] endpoint proxy error: {device_url}: {e}")
            return f"Failed to retrieve device endpoint: {endpoint}", 502

        if upstream.status_code != 200:
            status = upstream.status_code
            upstream.close()
            return f"Device endpoint returned HTTP {status}: {endpoint}", status

        content_type = upstream.headers.get('content-type', 'application/octet-stream')
        if content_type.startswith('multipart/'):
            def generate():
                try:
                    for chunk in upstream.iter_content(chunk_size=4096):
                        if chunk:
                            yield chunk
                finally:
                    upstream.close()
            return Response(stream_with_context(generate()), content_type=content_type)

        body = upstream.content
        upstream.close()
        return Response(body, content_type=content_type)


class SendCmd(Resource):
    """
    http://127.0.0.1:5005/sendcmd/micr240ac4f679e8OS/rgb+toggle
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
        if uid is None:
            abort(404, description=f"Unknown device: {device}")
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
        return {'cmd': cmd_list, 'device': device_detailed, 'response': response, 'latency': diff, 'state': bool(status)}


class ListDevices(Resource):
    DEVICE_CACHE = {}
    _THREAD_OBJ = None
    _LAST_EXEC_TIME = time.time()

    def sort_devices(self):
        device_struct = socketClient.ConnectionData.list_devices()
        online_devices = socketClient.ConnectionData.nodes_status(feature_stat=False)
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
            _status2, alarm_resp = socketClient.run(['--dev', fuid.strip(), 'system alarms dump=True >json'])
            if _status2:
                try:
                    alarms = json.loads(alarm_resp)
                    if not isinstance(alarms, dict) or 'health' not in alarms or 'verdict' not in alarms:
                        raise ValueError('invalid alarm response')
                except:
                    alarms = 'Unknown'
            if not isinstance(alarms, dict):
                _status2, alarm_resp = socketClient.run(['--dev', fuid.strip(), 'system alarms'])
                if _status2:
                    alarm_lines = alarm_resp.splitlines()
                    try:
                        verdict = alarm_lines[-1]
                        alarms = {'health': 'OK alarm' in verdict and 'NOK alarm' not in verdict,
                                  'verdict': verdict}
                    except:
                        alarms = {'health': False, 'verdict': "NOK"}

            # Clean Alarms
            clean_alarms = DeviceStatus.CLEAN_MICROS_ALARMS
            if clean_alarms and isinstance(alarms, dict) and alarms.get('health') is False:
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
            if isinstance(cpu_temp, str) and 'temp' in cpu_temp:
                try:
                    cpu_temp = cpu_temp.split(":")[1].strip()
                except:
                    pass
        return hwuid, status, fuid, devip, version, alarms, diff, upython_version, cpu_temp, free_fs, free_ram

    def get_all_node_status(self):
        output_dev_struct = {}
        online_dev_cnt = 0
        device_struct = socketClient.ConnectionData.list_devices()
        real_device_count = max(1, len(device_struct) - 2)
        dev_query_list = []

        # Start parallel status queries
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for uid in device_struct.keys():
                future = executor.submit(self.__get_node_status, device_struct, uid)
                dev_query_list.append(future)

        # Collect results from queries
        for query in dev_query_list:
            try:
                node_info = query.result()
            except Exception as e:
                print(f"Node status worker error: {e}")
                continue

            if node_info is None:
                continue
            # Unwrap data
            hwuid, status, fuid, devip, version, alarms, diff, upython_version, cpu_temp, free_fs, free_ram = node_info

            # Status calculation
            if status:
                online_dev_cnt += 1
                DeviceStatus.DEVS_AVAIL = round((online_dev_cnt / real_device_count) * 100, 1)
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
        index_html = os.path.join(WEBUI_PATH, 'img_stream.html')
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
api.add_resource(DeviceDashboardGroup, '/dashboard')
api.add_resource(DeviceDashboard, '/dashboard/<string:device>')
api.add_resource(DeviceDashboardRest,
                 '/dashboard/<string:device>/rest',
                 '/dashboard/<string:device>/rest/',
                 '/dashboard/<string:device>/rest/<path:cmd>')
api.add_resource(DeviceDashboardEndpoint, '/dashboard/<string:device>/<path:endpoint>')
api.add_resource(SendCmd, '/sendcmd/<string:device>/<string:cmd>')
api.add_resource(Prometheus, '/metrics/<string:device>/<string:cmd>')
api.add_resource(ForwardImg, '/image', '/image/<string:device>')
api.add_resource(ImgStream, '/imgstream')
api.add_resource(WebHook, '/webhooks', '/webhooks/<string:payload>', '/webhooks/<string:payload>/<string:args>')


def gateway(debug=True):
    if (__rest_usr_name and __rest_usr_pwd) and BasicAuth is None:
        raise RuntimeError("API_AUTH is set but flask_basicauth is unavailable. Refusing to start unsecured gateway.")
    global API_URL_CACHE
    API_URL_CACHE = f"http://{my_local_ip()}:5005"
    print("\n############### START MICROS GATEWAY ###############")
    print("#             {}            #".format(API_URL_CACHE))
    print("####################################################\n")
    app.run(debug=debug, use_reloader=debug, host='0.0.0.0', port=5005)     # host='0.0.0.0' automatic, manual: host=my_local_ip()


# driver function
if __name__ == '__main__':
    gateway()
