from urequests import get as http_get

class Rest:
    GATEWAY_HOST = None


def load_n_init(gateway_url=None):
    """
    Set gateway url aka main domain
    :param gateway_url: base url of gateway, like: http://gateway.local:5000
    """
    if gateway_url is None:
        if Rest.GATEWAY_HOST is None:
            return 'Missing Gateway url'
        return Rest.GATEWAY_HOST
    Rest.GATEWAY_HOST = gateway_url
    return f'Set gateway url: {gateway_url}'


def url(subdomain):
    """
    Execute rest call with given subdomain
    :param subdomain: command parameters of url, like: /webhooks/template
    """
    if Rest.GATEWAY_HOST is None:
        return 'Missing Gateway url'
    if not subdomain.startswith('/'):
        subdomain = '/' + subdomain
    domain = f'{Rest.GATEWAY_HOST}{subdomain}'
    status_code, response = http_get(domain, jsonify=True)
    return {'status': status_code, 'response': response}

def help(details=False):
    return 'load_n_init gateway_url=<http://gateway.local:5000>', 'url subdomain=</webhooks/template>'