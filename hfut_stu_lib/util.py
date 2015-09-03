# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import time
from logger import logger


def cal_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.clock()
        res = func(*args, **kwargs)
        logger.info('{:s} 执行用时: {:f}'.format(func.__name__, time.clock() - start_time))
        return res

    return wrapper


def unfinished(func):
    msg = '{:s} 尚未完成, 请勿尝试使用'.format(func.__name__)
    logger.error(msg)
    return func


def unstable(func):
    logger.warning('{:s} 功能尚不稳定, 请勿尝试使用'.format(func.__name__))
    return func
