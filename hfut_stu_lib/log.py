# -*- coding:utf-8 -*-
"""
日志模块
"""
from __future__ import unicode_literals

from logging import Logger, WARNING, StreamHandler, Formatter

__all__ = ['logger', 'unfinished', 'unstable']

logger = Logger('hfut_stu_lib', level=WARNING)

sh = StreamHandler()
fmt = Formatter('[%(levelname)s]%(filename)s[%(lineno)d]: %(message)s')
sh.setFormatter(fmt)
logger.addHandler(sh)


def unfinished(func):
    msg = '{:s} 尚未完成, 请勿尝试使用'.format(func.__name__)
    logger.error(msg)
    return func


def unstable(func):
    logger.warning('%s 功能尚不稳定, 建议使用时验证结果的正确性', func.__name__)
    return func
