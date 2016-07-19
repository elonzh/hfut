# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import re

HF = 'HF'
XC = 'XC'
HOSTS = {HF: 'http://bkjw.hfut.edu.cn/', XC: 'http://222.195.8.201/'}

TERM_PATTERN = re.compile(r'(\d{4})-\d{4}学年\s*第(一|二|二/三)学期(|/暑期)')
XC_PASSWORD_PATTERN = re.compile(r'^[\da-z]{6,12}$')
HF_PASSWORD_PATTERN = re.compile(r'^\S{6,16}$')
