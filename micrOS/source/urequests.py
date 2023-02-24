try:
    import usocket
    import ussl
    import ujson
except ImportError:
    import socket as usocket
    import ssl as ussl
    import json as ujson


def request(method, url, data=None, json=None, headers={}):
    # Parse URL
    proto, _, host, path = url.split('/', 3)
    port = 443 if proto == 'https:' else 80
    if ':' in host:
        host, port = host.split(':', 1)
        port = int(port)

    # Connect to host
    sock = usocket.socket()
    addr = usocket.getaddrinfo(host, port)[0][-1]
    sock.connect(addr)
    if proto == 'https:':
        sock = ussl.wrap_socket(sock)

    # Build request
    if data is not None:
        body = data.encode('utf-8')
        headers['Content-Length'] = len(body)
    elif json is not None:
        body = ujson.dumps(json).encode('utf-8')
        headers['Content-Length'] = len(body)
        headers['Content-Type'] = 'application/json'
    else:
        body = None
    lines = [f'{method} /{path} HTTP/1.1']
    for k, v in headers.items():
        lines.append(f'{k}: {v}')
    lines.append('Host: %s' % host)
    lines.append('Connection: close')
    request = '\r\n'.join(lines) + '\r\n\r\n'
    if body is not None:
        request += body.decode('utf-8')

    if proto == 'https:':
        sock.write(request.encode('utf-8'))
    else:
        # Send request
        sock.send(request.encode('utf-8'))

    # Receive response
    #response = sock.recv(4096)
    response = sock.read(4096)
    while True:
        #data = sock.recv(4096)
        data = sock.read(4096)
        if not data:
            break
        response += data
        print(data)
    sock.close()

    # Parse response
    headers, body = response.split(b'\r\n\r\n', 1)
    status_code = int(headers.split(b' ')[1])
    headers = dict(h.split(b': ') for h in headers.split(b'\r\n')[1:])
    if headers.get(b'Transfer-Encoding', b'') == b'chunked':
        body = decode_chunked(body)
    else:
        body = body.decode('utf-8')
    return Response(status_code, headers, body)


def get(url, headers={}):
    return request('GET', url, headers=headers)


def post(url, data=None, json=None, headers={}):
    return request('POST', url, data=data, json=json, headers=headers)


class Response:
    def __init__(self, status_code, headers, text):
        self.status_code = status_code
        self.headers = headers
        self.text = text

    def json(self):
        return ujson.loads(self.text)


def telegram_chat_id(token):
    host = "api.telegram.org"
    endpoint = "bot{token}/getUpdates".format(token=token)
    request = "GET /{} HTTP/1.0\r\nHost: {}\r\n\r\n".format(endpoint, host)

    sock = usocket.socket()
    sock.connect((host, 443))
    sock = ussl.wrap_socket(sock)
    sock.write(request.encode())

    data = b""
    while True:
        part = sock.read(1024)
        if not part:
            break
        data += part
    sock.close()

    #print(data)
    raw_response = data.decode()
    body_start = raw_response.find('{')
    body = raw_response[body_start:]
    response = ujson.loads(body)

    if response["ok"]:
        if len(response["result"]) > 0:
            chat_id = response["result"][-1]["message"]["chat"]["id"]
            return chat_id
    else:
        error_message = response.get("description", "Unknown error")
        raise Exception("Error retrieving chat ID: {}".format(error_message))
