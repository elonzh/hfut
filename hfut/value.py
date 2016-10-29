# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import re

HF = 'HF'
XC = 'XC'
HOSTS = {HF: 'http://bkjw.hfut.edu.cn/', XC: 'http://222.195.8.201/'}
SITE_ENCODING = 'GBK'
HTML_PARSER = 'html.parser'

# https://docs.python.org/3/library/re.html
TERM_PATTERN = re.compile(r'(\d{4})(?:|学年)-\d{4}学年\s*第(一|二|二/三)学期(|/暑期)')
ACCOUNT_PATTERN = re.compile(r'^\d{10}$')
# fixme: 这是教务密码规则, 并非宣城校区规则
XC_PASSWORD_PATTERN = re.compile(r'^[\da-z]{6,12}$')
HF_PASSWORD_PATTERN = re.compile(r'^[^\s,;*_?@#$%&()+=><]{6,16}$')

ILLEGAL_CHARACTERS_PATTERN = re.compile(r'[,;*_?@#$%&()+=><]')
