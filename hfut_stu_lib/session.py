# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import urlparse
import requests

from functools import update_wrapper

from . import SITE_ENCODING, HOST_URL
from .core import registered_api
from .logger import hfut_stu_lib_logger as logger


class AuthSession(requests.Session):
    def __init__(self, account=None, password=None, user_type='guest'):
        super(AuthSession, self).__init__()
        if user_type != 'guest' and not all([account, password]):
            raise ValueError('只有 user__type 为 guest 是才不用填写 account 和 password 参数')
        self.account = account
        self.password = password
        self.user_type = user_type
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0}'}
        self.login()
        # todo: 每次声明对象都会迭代一次模块, 效率极其低下
        self._setup_api()

    def __repr__(self):
        return '<AuthSession for {account:} ({user_type:})>'.format(account=self.account, user_type=self.user_type)

    def login(self):
        if self.user_type in ('student', 'teacher', 'admin'):
            login_url = urlparse.urljoin(HOST_URL, 'pass.asp')
            data = {"UserStyle": self.user_type, "user": self.account, "password": self.password}
            res = self.post(login_url, data=data, allow_redirects=False)
            if res.status_code != 302:
                raise ValueError('\n'.join(['登陆失败, 请检查你的账号和密码', res.request.body]))

    def _func2method(self, func):
        def _wrapper(*args, **kwargs):
            return func(self, *args, **kwargs)

        return update_wrapper(_wrapper, func)

    def _setup_api(self):
        for func_name, api_info in registered_api.iteritems():
            if api_info['user_type'] in (self.user_type, 'guest'):
                self.__setattr__(func_name, self._func2method(api_info['func']))
                logger.debug('{} 绑定给了 {}'.format(func_name, self.__repr__()))

    def catch_response(self, func_name, **kwargs):
        api_info = registered_api[func_name]
        method = api_info['method']

        url = urlparse.urljoin(HOST_URL, api_info['url'])
        logger.debug('{} 发出请求 {} {} {}'.format(func_name, method, url, kwargs or ''))
        res = self.request(method, url, **kwargs)
        res.encoding = SITE_ENCODING
        return res
