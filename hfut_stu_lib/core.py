# -*- coding:utf-8 -*-
from __future__ import unicode_literals
from functools import update_wrapper

from .logger import hfut_stu_lib_logger

registered_api = dict()


def unfinished(func):
    msg = '{:s} 尚未完成, 请勿尝试使用'.format(func.__name__)
    hfut_stu_lib_logger.error(msg)
    return func


def unstable(func):
    hfut_stu_lib_logger.warning('{:s} 功能尚不稳定, 建议使用时验证结果的正确性'.format(func.__name__))
    return func


def regist_api(url, method='get', user_type='guest'):
    def _dec(func):
        def _wrapper(session, *args, **kwargs):
            if session.user_type.lower() != user_type and user_type != 'guest':
                raise TypeError('用户类型不正确, session.user_type 应该为 {} 而不是 {}'
                                .format(user_type, session.user_type))
            else:
                return func(session, *args, **kwargs)

        w = update_wrapper(_wrapper, func)

        api_info = dict(url=url, method=method.lower(), user_type=user_type, func=w)
        registered_api[func.func_name] = api_info
        return w

    return _dec
