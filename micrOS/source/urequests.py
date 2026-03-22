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
from Debug import syslog
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
        line_end = _body.find(b"\r\n")
        if line_end < 0:
            break
        try:
            chunk_size = int(bytes(_body[:line_end]).decode('ascii'), 16)
        except ValueError:
            break
        if chunk_size == 0:
            break
        data_start = line_end + 2
        data_end = data_start + chunk_size
        decoded.extend(_body[data_start:data_end])
        if _body[data_end:data_end + 2] != b"\r\n":
            break
        _body = _body[data_end + 2:]
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
    body = b'' if data is None and json is None else \
           data.encode('utf-8') if data is not None else dumps(json).encode('utf-8')
    if body:
        headers['Content-Length'] = len(body)
    if json is not None:
        headers['Content-Type'] = 'application/json'

    req = bytearray(f'{method} /{path} HTTP/1.1\r\n'.encode('utf-8'))
    for k, v in headers.items():
        req.extend(f'{k}: {v}\r\n'.encode('utf-8'))
    req.extend(f'Host: {host}\r\nConnection: close\r\n\r\n'.encode('utf-8'))
    req.extend(body)
    return req


def _parse_response_head(raw):
    header_end = raw.find(b'\r\n\r\n')
    if header_end == -1:
        raise ValueError("Invalid HTTP response")
    headers_raw = bytes(raw[:header_end])
    status_code = int(headers_raw.split(b' ', 2)[1].decode('ascii'))
    headers = {}
    for line in headers_raw.split(b'\r\n')[1:]:
        if b': ' in line:
            key, value = line.split(b': ', 1)
            headers[key] = value
    return status_code, headers, header_end + 4


def _body_requires_more(headers, body):
    if headers.get(b'Transfer-Encoding', b'') == b'chunked':
        return not body.endswith(b'0\r\n\r\n')
    content_len = headers.get(b'Content-Length')
    if content_len is not None:
        return len(body) < int(content_len.decode('ascii'))
    return True


def _finalize_body(headers, body):
    if headers.get(b'Transfer-Encoding', b'') == b'chunked':
        return bytes(_chunked(body))
    content_len = headers.get(b'Content-Length')
    if content_len is not None:
        body = body[:int(content_len.decode('ascii'))]
    return body.decode('utf-8')


def _sock_write(sock, data):
    try:
        return sock.write(data)
    except AttributeError:
        return sock.send(data)


def _sock_read_factory(sock):
    return sock.read if hasattr(sock, "read") else sock.recv


def _read_response(receive, sock_size):
    raw = bytearray()
    while b'\r\n\r\n' not in raw:
        chunk = receive(sock_size)
        if not chunk:
            break
        raw.extend(chunk)
    status_code, headers, body_start = _parse_response_head(raw)
    body = raw[body_start:]
    while _body_requires_more(headers, body):
        chunk = receive(sock_size)
        if not chunk:
            break
        body.extend(chunk)
        if headers.get(b'Content-Length') is None and headers.get(b'Transfer-Encoding', b'') != b'chunked':
            continue
    return status_code, _finalize_body(headers, body)


async def _aread_response(reader, sock_size):
    raw = bytearray()
    while b'\r\n\r\n' not in raw:
        chunk = await reader.read(sock_size)
        if not chunk:
            break
        raw.extend(chunk)
    status_code, headers, body_start = _parse_response_head(raw)
    body = raw[body_start:]
    while _body_requires_more(headers, body):
        chunk = await reader.read(sock_size)
        if not chunk:
            break
        body.extend(chunk)
        if headers.get(b'Content-Length') is None and headers.get(b'Transfer-Encoding', b'') != b'chunked':
            continue
    return status_code, _finalize_body(headers, body)


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
        if proto == 'https:':
            try:
                sock = wrap_socket(sock, server_hostname=host)
            except TypeError:
                sock = wrap_socket(sock)
        else:
            sock = sock
    except Exception as e:
        syslog(f'[ERR] https soc-wrap: {e}')
        raise

    # [1] BUILD REQUEST
    http_request = _build_request(host, method, path, headers, data, json)

    # [2] SEND REQUEST
    try:
        _sock_write(sock, http_request)
        receive = _sock_read_factory(sock)

        # [3][4] RECEIVE + PARSE RESPONSE
        status_code, body = _read_response(receive, sock_size)
    finally:
        sock.close()

    # Return status code, body (text or json)
    if jsonify and status_code == 200:
        return status_code, loads(body.decode('utf-8') if isinstance(body, (bytes, bytearray)) else body)
    return status_code, body


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

    # Open a connection
    try:
        reader, writer = await asyncio.open_connection(addr[0], port, ssl=(proto == 'https:'))
    except Exception as e:
        # Refresh host address & reconnect
        if "EHOSTUNREACH" in str(e):
            addr = _host_to_addr(host, port, force=True)
            try:
                reader, writer = await asyncio.open_connection(addr[0], port, ssl=(proto == 'https:'))
            except Exception as e2:
                body = f"[ERR] arequest connection: {e2}"
                syslog(body)
                return 500, {} if jsonify else body
        else:
            body = f"[ERR] arequest connection: {e}"
            syslog(body)
            return 500, {} if jsonify else body

    # Send request + Wait for the response
    try:
        # Build the HTTP request
        http_request = _build_request(host, method, path, headers, data, json)

        # Send the request
        writer.write(http_request)
        await writer.drain()

        # Receive response
        status_code, body = await _aread_response(reader, sock_size)
    except Exception as e:
        status_code = 500
        # https://github.com/micropython/micropython/blob/8785645a952c03315dbf93667b5f7c7eec49762f/cc3200/simplelink/include/device.h
        if "-104" == str(e):
            body = "[WARN] arequest: ASSOC_REJECT"
        elif "ECONNABORTED" in str(e):
            body = f"[WARN] arequest: {e}"
        else:
            body = f"[ERR] arequest: {e}"
        syslog(body)
    finally:
        if writer:
            writer.close()
            await writer.wait_closed()
    if jsonify and status_code == 200:
        return status_code, loads(body.decode('utf-8') if isinstance(body, (bytes, bytearray)) else body)
    return status_code, body


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


def host_cache() -> dict:
    """
    Return address cache
    """
    return ADDR_CACHE
