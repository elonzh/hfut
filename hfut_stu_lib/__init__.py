# -*- coding:utf-8 -*-
"""
hfut_stu_lib
provided full-featured interfaces for the educational administration system of HeFei University of Technology.

hfut_stu_lib
提供了合肥工业大学教务系统学生端接口并提供了方便开发者开发围绕学生数据的一些工具.
"""
from __future__ import unicode_literals

__title__ = 'hfut_stu_lib'
__version__ = '1.1.0'
__author__ = 'erliang'
__author_email__ = 'dev@erliang.me'
__url__ = 'https://github.com/er1iang/hfut-stu-lib'
__license__ = 'MIT'
__copyright__ = 'Copyright 2015-2016 erliang'

ADMIN = 'admin'
STUDENT = 'student'
TEACHER = 'teacher'

HEFEI_HOST = 'http://bkjw.hfut.edu.cn/'
XUANCHENG_HOST = 'http://222.195.8.201/'

TERM_PATTERN = r'(\d{4})-\d{4}学年\s*第(一|二|二/三)学期(|/暑期)'
from .log import *
from .models import *
