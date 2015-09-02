# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import time
from logger import hfut_stu_lib_logger


def cal_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.clock()
        res = func(*args, **kwargs)
        hfut_stu_lib_logger.info('{:s} 执行用时: {:f}'.format(func.__name__, time.clock() - start_time))
        return res

    return wrapper
