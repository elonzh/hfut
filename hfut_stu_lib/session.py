# -*- coding:utf-8 -*-
from __future__ import unicode_literals, division
import requests
import six

from .const import HOST_URL, USER_TYPES, GUEST
from .core import all_api


class AuthSessionMeta(type):
    def __new__(mcs, name, bases, attrs):
        for api in all_api:
            attrs[api.__name__] = api
        return type.__new__(mcs, name, bases, attrs)


@six.add_metaclass(AuthSessionMeta)
class AuthSession(requests.Session):

    def __init__(self, account=None, password=None, user_type=GUEST):
        if user_type != GUEST and not all([account, password]):
            raise ValueError('非游客类型需要填写 account 和 password 参数')
        super(AuthSession, self).__init__()
        self.account = account
        self.password = password
        self.user_type = user_type
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0}'}
        # session 对象的 hooks 会在发送请求时被请求对象的 hooks 替换掉
        # self.hooks = dict(response=response_encoding)
        self.login()

    def __repr__(self):
        return '<AuthSession for {account} ({user_type})>'.format(account=self.account, user_type=self.user_type)

    def login(self):
        if self.user_type in USER_TYPES:
            login_url = six.moves.urllib.parse.urljoin(HOST_URL, 'pass.asp')
            data = {"UserStyle": self.user_type, "user": self.account, "password": self.password}
            res = self.post(login_url, data=data, allow_redirects=False)
            if res.status_code != 302:
                raise ValueError('\n'.join(['登陆失败, 请检查你的账号和密码', res.request.body]))

    def api_request(self, api_req_obj):
        prep = self.prepare_request(api_req_obj)
        proxies = api_req_obj.proxies or {}

        settings = self.merge_environment_settings(
            prep.url, proxies, api_req_obj.stream, api_req_obj.verify, api_req_obj.cert
        )

        # Send the request.
        send_kwargs = {
            'timeout': api_req_obj.timeout,
            'allow_redirects': api_req_obj.allow_redirects,
        }
        send_kwargs.update(settings)

        return self.send(prep, **send_kwargs)
