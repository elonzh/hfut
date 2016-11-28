# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import re

HF = 'HF'
XC = 'XC'
ENV = {
    HF: 'http://bkjw.hfut.edu.cn/',
    XC: 'http://222.195.8.201/',
    # 宣城校区教务地址, 只有第一个可以外网访问
    'XC_HOSTS': [
        'http://222.195.8.201/',
        'http://172.18.6.93/',
        'http://172.18.6.94/',
        'http://172.18.6.95/',
        'http://172.18.6.96/',
        'http://172.18.6.97/',
        'http://172.18.6.98/',
        'http://172.18.6.99/'
    ],
    # 默认请求头
    'DEFAULT_HEADERS': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/45.0.2454.101 Safari/537.36'
    },
    # 每个会话保存的历史记录最多数量
    'MAX_HISTORIES': 10,
    # 当状态响应码异常时是否触发错误
    'RAISE_FOR_STATUS': False,
    # 教务页面的编码
    'SITE_ENCODING': 'GBK',
    # 全局使用的 BeautifulSoup 特性, 可以通过改变此值修改 HTML 解析器
    'SOUP_FEATURES': 'html.parser',
    # 是否启用参数检查
    'REQUEST_ARGUMENTS_CHECK': True,
    # IP 禁用响应检查参数, 分别为响应体最小长度, 最大长度, 以及正则
    'IP_BANNED_RESPONSE': (320, 335, re.compile(r'SQL通用防注入系统')),
    # 非法字符正则
    'ILLEGAL_CHARACTERS_PATTERN': re.compile(r'[,;*@$]'),
    # 学期名称正则
    'TERM_PATTERN': re.compile(r'(\d{4})(?:|学年)-\d{4}学年\s*第(一|二|二/三)学期(|/暑期)', flags=re.UNICODE),
    # 登录学号正则
    'ACCOUNT_PATTERN': re.compile(r'^\d{10}$'),
    # 宣城校区登录账号正则
    'XC_PASSWORD_PATTERN': re.compile(r'^[\da-z]{6,12}$'),
    # 合肥校区登录账号正则
    'HF_PASSWORD_PATTERN': re.compile(r'^[^\s,;*_?@#$%&()+=><]{6,16}$'),
}
