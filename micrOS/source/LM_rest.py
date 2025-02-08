from urequests import get as http_get
from urequests import aget as http_aget
from Common import micro_task


class Rest:
    GATEWAY_HOST = None


def load(gateway_url=None):
    """
    Set gateway url aka main domain
    :param gateway_url: base url of gateway, like: http://gateway.local:5000
    """
    if gateway_url is None:
        if Rest.GATEWAY_HOST is None:
            return 'Missing Gateway url'
        return Rest.GATEWAY_HOST
    if gateway_url.startswith("http"):
        Rest.GATEWAY_HOST = gateway_url
    else:
        return f"URL have to starts with http/https"
    return f'Gateway url: {gateway_url}'


def _subdomain(subdomain):
    if Rest.GATEWAY_HOST is None:
        raise Exception('Missing Gateway url')
    if not subdomain.startswith('/'):
        subdomain = '/' + subdomain
    domain = f'{Rest.GATEWAY_HOST}{subdomain}'
    return domain


def url(subdomain):
    """
    Execute rest call with given subdomain / url
    :param subdomain: url parameter,  http(s) full url or gateway subdomain like: /webhooks/template
    """
    if subdomain.startswith('http'):
        domain = subdomain
    else:
        domain = _subdomain(subdomain)
    status_code, response = http_get(domain, jsonify=True)
    return {'status': status_code, 'response': response}


async def __task(subdomain, tag):
    with micro_task(tag=tag) as my_task:
        my_task.out = f"GET {subdomain}"
        if subdomain.startswith('http'):
            domain = subdomain
        else:
            domain = _subdomain(subdomain)
        status_code, response = await http_aget(domain, jsonify=True)
        my_task.out = f'status: {status_code}, response: {response}'
    return {'status': status_code, 'response': response}


def aurl(subdomain):
    """
    Execute async rest call with given subdomain / url
    :param subdomain: url parameter,  http(s) full url or gateway subdomain like: /webhooks/template
    """
    # [!] ASYNC TASK CREATION [1*] with async task callback + taskID (TAG) handling
    tag = "rest." + subdomain.replace("http://", '').replace("https://", '')
    if len(tag) > 50:
        tag = tag[0:50]
    state = micro_task(tag=tag, task=__task(subdomain, tag))
    return f"Starting" if state else f"Already running"


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return ('load gateway_url=<http://gateway.local:5000>',
            'url subdomain=</webhooks/template>',
            'aurl subdomain=</webhooks/template>')