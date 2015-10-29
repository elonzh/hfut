# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import urlparse
import requests

from . import SITE_ENCODING, HOST_URL, USER_TYPES, GUEST
from .core import g
from .logger import hfut_stu_lib_logger as logger


# todo: 整个缓存功能待写单元测试
class AuthSessionMeta(type):
    def __new__(mcs, name, bases, attrs):
        for func_name, api_info in g.registered_api.iteritems():
            attrs[func_name] = api_info['func']
        return type.__new__(mcs, name, bases, attrs)


class AuthSession(requests.Session):
    __metaclass__ = AuthSessionMeta

    def __init__(self, account=None, password=None, user_type=GUEST):
        super(AuthSession, self).__init__()
        if user_type != GUEST and not all([account, password]):
            raise ValueError('只有 user__type 为 GUEST 是才不用填写 account 和 password 参数')
        self.account = account
        self.password = password
        self.user_type = user_type
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0}'}
        self.login()

    def __repr__(self):
        return '<AuthSession for {account} ({user_type})>'.format(account=self.account, user_type=self.user_type)

    def login(self):
        if self.user_type in USER_TYPES:
            login_url = urlparse.urljoin(HOST_URL, 'pass.asp')
            data = {"UserStyle": self.user_type, "user": self.account, "password": self.password}
            res = self.post(login_url, data=data, allow_redirects=False)
            if res.status_code != 302:
                raise ValueError('\n'.join(['登陆失败, 请检查你的账号和密码', res.request.body]))

    def catch_response(self, func_name, **kwargs):
        api_info = g.registered_api[func_name]
        method = api_info['method']

        url = urlparse.urljoin(HOST_URL, api_info['url'])
        logger.debug('{} 发出请求 {} {} {}'.format(func_name, method, url, kwargs or ''))
        res = self.request(method, url, **kwargs)
        res.encoding = SITE_ENCODING
        return res
