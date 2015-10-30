# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

__title__ = 'hfut_stu_lib'
__version__ = '0.3.1'
__author__ = 'erliang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2015 erliang'

from . import api
from .core import g
from .const import *
from .session import AuthSession
from .logger import hfut_stu_lib_logger

try:
    import uniout
except ImportError:
    hfut_stu_lib_logger.info('安装 uniout 库能够直接显示 unicode 内容')
