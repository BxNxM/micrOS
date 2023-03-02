try:
    import usocket
    import ussl
    import ujson
except ImportError:
    import socket as usocket
    import ssl as ussl
    import json as ujson


#############################################
#   Implement micropython request function  #
#############################################


def request(method, url, data=None, json=None, headers={}, sock_size=1024):
    """
    Micropython HTTP request function for REST API handling
    :param method: GET/POST
    :param url: URL for REST API
    :param data: string body
    :param json: json body
    :param headers: define headers
    :param sock_size: socket buffer size, default 1024 byte (micropython)
    """

    # [1] PARSE URL -> proto (http/https), host, path + SET PORT
    proto, _, host, path = url.split('/', 3)
    port = 443 if proto == 'https:' else 80
    # [1.1] PARSE HOST - handle direct port number as input after :
    if ':' in host:
        host, port = host.split(':', 1)
        port = int(port)

    # [2] CONNECT - create socket object
    sock = usocket.socket()
    sock.settimeout(2)
    # [2.1] CONNECT - resolve IP by host
    addr = usocket.getaddrinfo(host, port)[0][-1]
    # [2.2] CONNECT - if https handle ssl
    sock.connect(addr)
    if proto == 'https:':
        sock = ussl.wrap_socket(sock)

    # [3] BUILD REQUEST: body, headers
    if data is not None:
        body = data.encode('utf-8')
        headers['Content-Length'] = len(body)
    elif json is not None:
        body = ujson.dumps(json).encode('utf-8')
        headers['Content-Length'] = len(body)
        headers['Content-Type'] = 'application/json'
    else:
        body = None
    # [3.1] Create request lines list (body)
    lines = [f'{method} /{path} HTTP/1.1']
    for k, v in headers.items():
        lines.append(f'{k}: {v}')
    lines.append('Host: %s' % host)
    lines.append('Connection: close')
    request = '\r\n'.join(lines) + '\r\n\r\n'
    if body is not None:
        request += body.decode('utf-8')

    # [4] SEND REQUEST
    if proto == 'https:':
        sock.write(request.encode('utf-8'))
    else:
        # Send request
        sock.send(request.encode('utf-8'))

    # [5] RECEIVE RESPONSE
    #response = sock.recv(sock_size)
    response = sock.read(sock_size)
    while True:
        #data = sock.recv(sock_size)
        data = sock.read(sock_size)
        if not data:
            break
        response += data
        print("RAW DATA STREAM: {}".format(data))
    sock.close()

    # [6] PARSE RESPONSE
    headers, body = response.split(b'\r\n\r\n', 1)
    status_code = int(headers.split(b' ')[1])
    headers = dict(h.split(b': ') for h in headers.split(b'\r\n')[1:])
    if headers.get(b'Transfer-Encoding', b'') == b'chunked':
        body = decode_chunked(body)
    else:
        body = body.decode('utf-8')
    return Response(status_code, headers, body)


class Response:
    """
    micropython Request response data structure
    Data:
    - status_code
    - headers
    - text
    Method:
    - json parser function
    """
    def __init__(self, status_code, headers, text):
        self.status_code = status_code
        self.headers = headers
        self.text = text

    def json(self):
        return ujson.loads(self.text)


#############################################
#      Implement http get/post functions    #
#############################################


def get(url, headers={}):
    return request('GET', url, headers=headers)


def post(url, data=None, json=None, headers={}):
    return request('POST', url, data=data, json=json, headers=headers)
