"""
This module implements an optimized version of requests module
for async and sync http get and post requests.

Designed by Marcell Ban aka BxNxM GitHub
"""

from json import loads, dumps
from usocket import socket, getaddrinfo
try:
    from ussl import wrap_socket    # Legacy micropython ssl usage (+simulator mode)
except ImportError:
    from ssl import wrap_socket     # From micropython 1.23...
from Debug import errlog_add
import uasyncio as asyncio


ADDR_CACHE = {}

#############################################
#  micropython request - helper functions   #
#############################################


def _host_to_addr(host, port, force=False):
    """
    Resolve host name to IP address
    and cache host address to avoid slow getaddrinfo
    """
    addr = ADDR_CACHE.get(host, None)
    if addr is None or force:
        addr = getaddrinfo(host, port)[0][-1]
        ADDR_CACHE[host] = addr
    return addr


def _chunked(_body):
    decoded = bytearray()
    while _body:
        # Find the end of the chunk size line
        line_end = _body.find(b"\r\n")
        if line_end < 0:
            break

        # Extract the chunk size and convert to int
        chunk_size_str = _body[:line_end]
        try:
            chunk_size = int(chunk_size_str, 16)
        except ValueError:
            chunk_size = 0

        # Check chunk size
        if chunk_size == 0:
            break

        # Add the chunk data to the decoded data
        chunk_data = _body[line_end + 2: line_end + 2 + chunk_size]
        decoded += chunk_data

        # Move to the next chunk
        _body = _body[line_end + 4 + chunk_size:]

        # Check for end of message marker again
        if not _body.startswith(b"\r\n"):
            break
    return decoded


def _parse_url(url):
    # PARSE URL -> proto (http/https), host, path + SET PORT
    proto, _, host, path = url.split('/', 3)
    port = 443 if proto == 'https:' else 80
    # PARSE HOST - handle direct port number as input after :
    if ':' in host:
        host, port = host.split(':', 1)
        port = int(port)
    return host, port, proto, path


def _build_request(host, method, path, headers, data=None, json=None):
    # Create request (body, headers)
    body = None
    if data:
        body = data.encode('utf-8')
        headers['Content-Length'] = len(body)
    elif json:
        body = dumps(json).encode('utf-8')
        headers['Content-Length'] = len(body)
        headers['Content-Type'] = 'application/json'

    # [3.1] Create request lines list (body)
    lines = [f'{method} /{path} HTTP/1.1']
    for k, v in headers.items():
        lines.append(f'{k}: {v}')
    lines.append('Host: %s' % host)
    lines.append('Connection: close')
    http_request = '\r\n'.join(lines) + '\r\n\r\n'
    if body:
        http_request += body.decode('utf-8')
    return http_request


def _parse_response(response):
    # Parse response - get body
    headers, body = response.split(b'\r\n\r\n', 1)
    status_code = int(headers.split(b' ')[1])
    headers = dict(h.split(b': ') for h in headers.split(b'\r\n')[1:])
    if headers.get(b'Transfer-Encoding', b'') == b'chunked':
        body = _chunked(body)
    else:
        body = body.decode('utf-8')
    return status_code, body


#############################################
#          micropython HTTP request         #
#############################################

def request(method:str, url:str, data:str=None, json=None, headers:dict=None, sock_size=256, jsonify=False):
    """
    Micropython syncronous HTTP request function for REST API handling
    :param method: GET/POST
    :param url: URL for REST API
    :param data: string body (handle bare string as data for POST method)
    :param json: json body (handle json as data for POST method)
    :param headers: define headers
    :param sock_size: socket buffer size (chuck size), default 256 byte (micropython defualt)
    :param jsonify: convert response body to json
    """

    # Parse HTTP(S) URL and headers
    headers = {} if headers is None else headers
    host, port, proto, path = _parse_url(url)
    addr = _host_to_addr(host, port)

    # [1] CONNECT - create socket object
    sock = socket()
    sock.settimeout(3)
    # [1.1] CONNECT - if https handle ssl
    try:
        sock.connect(addr)
    except Exception:
        # Refresh host address & reconnect
        addr = _host_to_addr(host, port, force=True)
        sock.connect(addr)

    try:
        sock = wrap_socket(sock) if proto == 'https:' else sock
    except Exception as e:
        errlog_add(f'[ERR] https soc-wrap: {e}')

    # [1] BUILD REQUEST
    http_request = _build_request(host, method, path, headers, data, json)

    # [2] SEND REQUEST
    if proto == 'https:':
        sock.write(http_request.encode('utf-8'))    # Send request (secure)
        receive = sock.read                         # Save Read object (secure)
    else:
        # Send request
        sock.send(http_request.encode('utf-8'))     # Send request
        receive = sock.recv                         # Save Read object

    # [3] RECEIVE RESPONSE
    response = receive(sock_size)
    while True:
        data = receive(sock_size)
        if not data:
            break
        response += data
    sock.close()

    # [4] PARSE RESPONSE
    status_code, body = _parse_response(response)

    # Return status code, body (text or json)
    return status_code, loads(body) if jsonify and status_code == 200 else body


#############################################
#       async micropython HTTP request      #
#############################################

async def arequest(method:str, url:str, data:str=None, json=None, headers:dict=None, sock_size=256, jsonify=False):
    """
    Micropython asynchronous HTTP request function for REST API handling
    :param method: GET/POST
    :param url: URL for REST API
    :param data: string body (handle bare string as data for POST method)
    :param json: json body (handle json as data for POST method)
    :param headers: define headers
    :param sock_size: socket buffer size (chunk size), default 256 bytes (micropython default)
    :param jsonify: convert response body to json
    """
    headers = {} if headers is None else headers
    host, port, proto, path = _parse_url(url)
    addr = _host_to_addr(host, port)
    reader, writer = None, None

    try:
        # Open a connection
        reader, writer = await asyncio.open_connection(addr[0], port, ssl=(proto == 'https:'))

        # Build the HTTP request
        http_request = _build_request(host, method, path, headers, data, json)

        # Send the request
        writer.write(http_request.encode('utf-8'))
        await writer.drain()

        # Receive response
        response = b''
        while True:
            chunk = await reader.read(sock_size)
            if not chunk:
                break
            response += chunk

        # Parse response
        status_code, body = _parse_response(response)
    except Exception as e:
        status_code = 500
        # https://github.com/micropython/micropython/blob/8785645a952c03315dbf93667b5f7c7eec49762f/cc3200/simplelink/include/device.h
        if "-104" == str(e):
            body = "[WARN] arequest: ASSOC_REJECT"
        elif "ECONNABORTED" in str(e):
            body = f"[WARN] arequest: {e}"
        else:
            body = f"[ERR] arequest: {e}"
        errlog_add(body)
    finally:
        if writer:
            writer.close()
            await writer.wait_closed()
    return status_code, loads(body) if jsonify and status_code == 200 else body


#############################################
#      Implement http get/post functions    #
#############################################

def get(url:str, headers:dict=None, sock_size=256, jsonify=False):
    """
    GENERIC HTTP GET FUNCTION
    """
    if headers is None:
        headers = {}
    return request('GET', url, headers=headers, sock_size=sock_size, jsonify=jsonify)


def post(url:str, data=None, json=None, headers:dict=None, sock_size=256, jsonify=False):
    """
    GENERIC HTTP POST FUNCTION
    :param data: string body (handle bare string as data for POST method)
    :param json: json body (handle json as data for POST method)
    """
    return request('POST', url, data=data, json=json, headers=headers, sock_size=sock_size, jsonify=jsonify)


async def aget(url:str, headers:dict=None, sock_size=256, jsonify=False):
    """
    GENERIC ASYNC HTTP GET FUNCTION
    """
    return await arequest('GET', url, headers=headers, sock_size=sock_size, jsonify=jsonify)


async def apost(url, data=None, json=None, headers:dict=None, sock_size=256, jsonify=False):
    """
    GENERIC ASYNC HTTP POST FUNCTION
    :param data: string body (handle bare string as data for POST method)
    :param json: json body (handle json as data for POST method)
    """
    return await arequest('POST', url, data=data, json=json, headers=headers, sock_size=sock_size, jsonify=jsonify)


def host_cache():
    """
    Return address cache
    """
    return ADDR_CACHE
