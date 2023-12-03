try:
    from usocket import socket, getaddrinfo
    from ussl import wrap_socket
except ImportError as e:
    print(f"[Error] import u modules: {e}")
    from socket import socket, getaddrinfo
    from ssl import wrap_socket
from json import loads, dumps
from Debug import errlog_add


ADDR_CACHE = {}


def request(method, url, data=None, json=None, headers=None, sock_size=256, jsonify=False):
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

    #############################################
    # micropython request - internal functions  #
    #############################################
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
            except ValueError as e:
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

    def _host_to_addr(force=False):
        """
        Cache host address to avoid getaddrinfo (slow)
        """
        nonlocal host, port
        _addr = ADDR_CACHE.get(host, None)
        if _addr is None or force:
            _addr = getaddrinfo(host, port)[0][-1]
            ADDR_CACHE[host] = _addr
        return _addr

    #############################################
    #           micropython request main        #
    #############################################

    # [_parse_url] Parse HTTP(S) URL
    headers = {} if headers is None else headers
    # PARSE URL -> proto (http/https), host, path + SET PORT
    proto, _, host, path = url.split('/', 3)

    port = 443 if proto == 'https:' else 80
    # PARSE HOST - handle direct port number as input after :
    if ':' in host:
        host, port = host.split(':', 1)
        port = int(port)

    # [1] CONNECT - create socket object
    sock = socket()
    sock.settimeout(3)
    # [1.1] CONNECT - resolve IP by host
    addr = _host_to_addr()
    # [1.2] CONNECT - if https handle ssl
    try:
        sock.connect(addr)
    except Exception:
        # Refresh host address & reconnect
        addr = _host_to_addr(force=True)
        sock.connect(addr)

    try:
        sock = wrap_socket(sock) if proto == 'https:' else sock
    except Exception as e:
        errlog_add(f'[ERR] https soc-wrap: {e}')

    # [_build_request] Create request (body, headers)
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

    # [_parse_response] Parse response - get body
    headers, body = response.split(b'\r\n\r\n', 1)
    status_code = int(headers.split(b' ')[1])
    headers = dict(h.split(b': ') for h in headers.split(b'\r\n')[1:])
    if headers.get(b'Transfer-Encoding', b'') == b'chunked':
        body = _chunked(body)
    else:
        body = body.decode('utf-8')

    # Return status code, headers and body (text or jsons)
    return status_code, loads(body) if jsonify else body


#############################################
#      Implement http get/post functions    #
#############################################


def get(url, headers={}, sock_size=256, jsonify=False):
    """
    GENERIC HTTP GET FUNCTION
    """
    return request('GET', url, headers=headers, sock_size=sock_size, jsonify=jsonify)


def post(url, data=None, json=None, headers={}, sock_size=256, jsonify=False):
    """
    GENERIC HTTP POST FUNCTION
    :param data: string body (handle bare string as data for POST method)
    :param json: json body (handle json as data for POST method)
    """
    return request('POST', url, data=data, json=json, headers=headers, sock_size=sock_size, jsonify=jsonify)


def host_cache():
    """
    Return address cache
    """
    return ADDR_CACHE
