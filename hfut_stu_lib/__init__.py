# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import sys

reload(sys)
sys.setdefaultencoding('utf-8')
try:
    import uniout
except ImportError:
    logger.info('安装 uniout 库能够直接显示 unicode 内容')

from . import api
from .core import g
from .session import AuthSession
from .logger import hfut_stu_lib_logger as logger

__title__ = 'hfut_stu_lib'
__version__ = '0.3.0'
__author__ = 'erliang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2015 erliang'

SITE_ENCODING = 'gbk'
HOST_URL = 'http://222.195.8.201/'

GUEST = 'guest'
STUDENT = 'student'
TEACHER = 'teacher'
ADMIN = 'admin'
USER_TYPES = (STUDENT, TEACHER, ADMIN)
