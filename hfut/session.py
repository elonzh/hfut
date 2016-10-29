# -*- coding:utf-8 -*-
"""
会话管理模块, 在 ``requests.Session`` 的基础上添加了一些针对接口的改进
"""
from __future__ import unicode_literals, division

import time
from collections import deque

import requests
import six

from .exception import SystemLoginFailed, IPBanned
from .value import HF, HOSTS, SITE_ENCODING

__all__ = ['BaseSession', 'GuestSession', 'StudentSession']


class BaseSession(requests.Session):
    """
    所有接口会话类的基类
    """
    host = None
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/45.0.2454.101 Safari/537.36'
    }
    histories = deque(maxlen=10)

    def __init__(self, campus):
        """
        所以接口会话类的基类

        :param campus: 校区代码, 请使用 ``value`` 模块中的 ``HF``, ``XC`` 分别来区分合肥校区和宣城校区
        """
        super(BaseSession, self).__init__()
        self.headers = self.default_headers

        # 初始化时根据合肥选择不同的地址
        self.campus = campus.upper()
        self.host = HOSTS[self.campus]

    def prepare_request(self, request):
        # requests 在准备 url 进行解析, 因此只能在准备前将 url 换成完整的地址
        # requests.models.PreparedRequest#prepare_url
        if not six.moves.urllib.parse.urlparse(request.url).netloc:
            request.url = six.moves.urllib.parse.urljoin(self.host, request.url)
        return super(BaseSession, self).prepare_request(request)

    def send(self, request, **kwargs):
        """
        所有接口用来发送请求的方法, 只是 :meth:`requests.sessions.Session.send` 的一个钩子方法, 用来处理请求前后的工作
        """
        response = super(BaseSession, self).send(request, **kwargs)
        response.encoding = SITE_ENCODING
        self.histories.append(response)
        return response


class GuestSession(BaseSession):
    pass


@six.python_2_unicode_compatible
class StudentSession(BaseSession):
    """
    学生教务接口, 继承了 :class:`models.GuestSession` 的所有接口, 因此一般推荐使用这个类
    """

    def __init__(self, account, password, campus):
        """
        :param account: 学号
        :param password: 密码
        """
        # 先初始化状态才能登陆
        super(StudentSession, self).__init__(campus)

        self.account = account
        self.password = password
        self.name = None
        self.last_request_at = 0

    def request(self, *args, **kwargs):
        if self.is_expired:
            self.login()
        self.last_request_at = time.time()

        return super(StudentSession, self).request(*args, **kwargs)

    def __str__(self):
        return '<StudentSession:{account}>'.format(account=self.account)

    @property
    def is_expired(self):
        """
        asp.net 如果程序中没有设置session的过期时间,那么session过期时间就会按照IIS设置的过期时间来执行,
        IIS中session默认过期时间为20分钟,网站配置 最长24小时,最小15分钟, 页面级>应用程序级>网站级>服务器级.
        .那么当超过 15 分钟未操作会认为会话已过期需要重新登录

        :return: 会话是否过期
        """
        now = time.time()
        return (now - self.last_request_at) >= 900

    def login(self):
        """
        登录账户
        """
        # 登陆前清空 cookie, 能够防止再次登陆时因携带 cookie 可能提示有未进行教学评估的课程导致接口不可用
        self.cookies.clear_session_cookies()

        if self.campus == HF:
            login_data = {'IDToken1': self.account, 'IDToken2': self.password}
            login_url = 'http://ids1.hfut.edu.cn/amserver/UI/Login'
            super(StudentSession, self).request('post', login_url, data=login_data)

            method = 'get'
            url = 'StuIndex.asp'
            data = None
        else:
            method = 'post'
            url = 'pass.asp'
            data = {"user": self.account, "password": self.password, "UserStyle": 'student'}
        # 使用重载的 request 会造成递归调用
        response = super(StudentSession, self).request(method, url, data=data, allow_redirects=False)
        logged_in = response.status_code == 302
        if not logged_in:
            if 'SQL通用防注入系统' in response.text:
                msg = '当前 IP 已被锁定,如果是宣城校内访问请切换教务系统地址,否则请在更换网络环境后重试'
                raise IPBanned(msg)
            else:
                msg = '登陆失败, 请检查你的账号和密码'
                raise SystemLoginFailed(msg)

        escaped_name = self.cookies.get('xsxm')
        # https://pythonhosted.org/six/#module-six.moves.urllib.parse
        if six.PY3:
            self.name = six.moves.urllib.parse.unquote(escaped_name, SITE_ENCODING)
        else:
            name = six.moves.urllib.parse.unquote(escaped_name)
            self.name = name.decode(SITE_ENCODING)
