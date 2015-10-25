# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import sys

reload(sys)
sys.setdefaultencoding('utf-8')

__title__ = 'hfut_stu_lib'
__version__ = '0.2.0'
__author__ = 'erliang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2015 erliang'

SITE_ENCODING = 'gbk'
HOST_URL = 'http://222.195.8.201/'

from . import api
from .core import regist_api, registered_api
from .session import AuthSession
