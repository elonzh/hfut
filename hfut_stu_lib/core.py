# -*- coding:utf-8 -*-
from __future__ import unicode_literals, division

from .logger import hfut_stu_lib_logger

# 外层局部作用域对象只能应用不能修改, 所以将这三个变量封装了进去
all_api = []


def unfinished(func):
    msg = '{:s} 尚未完成, 请勿尝试使用'.format(func.__name__)
    hfut_stu_lib_logger.error(msg)
    return func


def unstable(func):
    hfut_stu_lib_logger.warning('%s 功能尚不稳定, 建议使用时验证结果的正确性', func.__name__)
    return func


def register_api(func):
    all_api.append(func)
    return func
