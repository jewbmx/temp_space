

import re

import six
from six.moves.urllib_parse import unquote_plus, quote_plus, urlencode

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.packages.urllib3.exceptions import InsecurePlatformWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)

import ssl


_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0'
_SESSION = None
_REFERER_HEADER = "Referer"
_COOKIE_HEADER = "Cookie"
_HEADER_RE = re.compile("^([\w\d-]+?)=(.*?)$")


class SSLAdapter(HTTPAdapter):
    '''An HTTPS Transport Adapter that uses an arbitrary SSL version.'''
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize, block=block)


class PrepReq(object):
    def __init__(self, session):
        self._dict = {}
        self._cookies = session.cookies


    def add_header(self, key, value):
        self._dict[key] = value


    def add_cookie(self, key, value):
        self._cookies.update({key: value})


    @property
    def headers(self):
        return self._dict


    @property
    def cookies(self):
        return self._cookies.keys()


def Session():
    global _SESSION
    if not _SESSION:
        s = requests.Session()
        s.mount('https://', SSLAdapter())
        s.headers.update({
            'User-Agent': _USER_AGENT,
        })
        _SESSION = s
    return _SESSION


def __set_header(set_request, header_name, header_value):
    def f(req):
        if set_request is not None:
            req = set_request(req)
        req.add_header(header_name, header_value)
        return req
    return f


def __set_referer(set_request, url):
    return __set_header(set_request, _REFERER_HEADER, url)


def __set_cookie(set_request, c):
    return __set_header(set_request, _COOKIE_HEADER, c)


def __send_request(session, url, data=None, set_request=None, head=False):
    r = PrepReq(session)
    if set_request:
        r = set_request(r)
    kargs = {
        'headers': r.headers,
        'verify': False,
        'url': url,
        'allow_redirects': True,
    }
    if head:
        return session.head(**kargs)
    if data:
        data = urlencode(data)
        return session.post(data=data, **kargs)
    return session.get(**kargs)


def _url_with_headers(url, headers):
    if not len(headers.keys()):
        return url
    headers_arr = ["%s=%s" % (key, quote_plus(value)) for key, value in six.iteritems(headers)]
    return "|".join([url] + headers_arr)


def _strip_url(url):
    if url.find('|') == -1:
        return (url, {})
    headers = url.split('|')
    target_url = headers.pop(0)
    out_headers = {}
    for h in headers:
        m = _HEADER_RE.findall(h)
        if not len(m):
            continue
        out_headers[m[0][0]] = unquote_plus(m[0][1])
    return (target_url, out_headers)


def raw_url(url):
    return _strip_url(url)[0]


def get_referer(url):
    url, headers = _strip_url(url)
    if _REFERER_HEADER in headers:
        return headers[_REFERER_HEADER]
    return None


def add_referer_url(url, referer):
    url, headers = _strip_url(url)
    headers[_REFERER_HEADER] = referer
    return _url_with_headers(url, headers)


def strip_cookie_url(url):
    url, headers = _strip_url(url)
    if _COOKIE_HEADER in headers.keys():
        del headers[_COOKIE_HEADER]
    return _url_with_headers(url, headers)


def head_request(url, set_request=None):
    return send_request(url, set_request=set_request, head=True)


def send_request(url, data=None, set_request=None, head=False):
    session = Session()
    target_url, headers = _strip_url(url)
    refer_url = None
    out_headers = {}
    for header, value in six.iteritems(headers):
        if header == _REFERER_HEADER:
            refer_url = value
        elif header == _COOKIE_HEADER:
            cookie = value
            set_request = __set_cookie(set_request, cookie)
        else:
            out_headers[header] = value
    if refer_url:
        set_request = __set_referer(set_request, refer_url)
    resp = __send_request(session, target_url, data, set_request, head)
    cookie = resp.request.headers.get(_COOKIE_HEADER)
    if cookie:
        out_headers[_COOKIE_HEADER] = cookie
    refer_url = resp.request.headers.get(_REFERER_HEADER)
    if refer_url:
        out_headers[_REFERER_HEADER] = refer_url
    resp.url = _url_with_headers(resp.url, out_headers)
    return resp


