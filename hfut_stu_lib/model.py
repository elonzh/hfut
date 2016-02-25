# -*- coding:utf-8 -*-
from __future__ import unicode_literals, print_function, division

import json
import requests
import six

from pprint import pformat
from abc import abstractmethod

from .const import HOST_URL
from .hooks import response_encoding


class APIRequestBuilder(object):
    # 指定用户类型用来区别是否需要登录
    user_type = None

    # 请求对象参数
    method = None
    url = None

    data = None
    params = None

    headers = None
    cookies = None
    auth = None
    files = None
    json = None

    proxies = None
    stream = None
    verify = None
    cert = None

    timeout = None
    allow_redirects = True

    hooks = None

    @abstractmethod
    def after_response(self, response, *args, **kwargs):
        """
        :param response: requests.Response
        :type response: requests.Response
        :param args: hook args
        :param kwargs: hook kwargs
        :return: APIResult
        :rtype: APIResult
        """
        raise NotImplementedError('必须实现 after_response !')

    @property
    def api_req_obj_args(self):
        """
        :return: api_req_obj_args
        :rtype: dict
        """
        all_attrs = ('method', 'url', 'headers', 'files', 'data', 'params', 'auth', 'cookies', 'hooks', 'json',
                     'proxies', 'stream', 'verify', 'cert',
                     'timeout', 'allow_redirects')
        if not six.moves.urllib.parse.urlparse(self.url).netloc:
            self.url = six.moves.urllib.parse.urljoin(HOST_URL, self.url)
        kwargs = {k: self.__getattribute__(k) for k in all_attrs if hasattr(self, k) and self.__getattribute__(k)}
        kwargs.setdefault('hooks', dict())
        kwargs['hooks'].setdefault('response', [response_encoding, self.after_response])

        return kwargs

    def gen_api_req_obj(self):
        """
        :return: api_req_obj
        :rtype: APIResult
        """
        kwargs = self.api_req_obj_args
        return APIRequest(**kwargs)


@six.python_2_unicode_compatible
class APIRequest(requests.Request):
    def __init__(self, proxies=None, stream=None, verify=None, cert=None, timeout=None, allow_redirects=True,
                 **request_kwargs):
        self.proxies = proxies
        self.stream = stream
        self.verify = verify
        self.cert = cert
        self.timeout = timeout
        self.allow_redirects = allow_redirects
        super(APIRequest, self).__init__(**request_kwargs)

    def __str__(self):
        return '<APIRequest [{:s}] {:s}>'.format(self.method, self.url)


@six.python_2_unicode_compatible
class APIResult(object):
    def __init__(self, response, data=None):
        super(APIResult, self).__init__()
        self.response = response
        self.data = data

    def __str__(self):
        return '\n'.join(['<APIResult> [{:s}] {:s}'.format(self.request.method, self.url), pformat(self.data)])

    def __getattr__(self, item):
        return self.__dict__.get(item) or self.response.__getattribute__(item)

    def json(self):
        return json.dumps(self.data)
