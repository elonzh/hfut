# -*- coding:utf-8 -*-
from __future__ import unicode_literals
from functools import wraps

from . import GUEST
from .logger import hfut_stu_lib_logger as logger
from .util import cal_cache_md5

# 外层局部作用域对象只能应用不能修改, 所以将这三个变量封装了进去
g = type(str('g'), (object,), dict(registered_api={}, cached_api={}, current_cache_manager=None))()


def unfinished(func):
    msg = '{:s} 尚未完成, 请勿尝试使用'.format(func.__name__)
    logger.error(msg)
    return func


def unstable(func):
    logger.warning('{:s} 功能尚不稳定, 建议使用时验证结果的正确性'.format(func.__name__))
    return func


def register_api(url, method='get', user_type=GUEST):
    def _register_dec(func):

        @wraps(func)
        def registered_api_wrapper(session, *args, **kwargs):
            if session.user_type.lower() != user_type and user_type != GUEST:
                raise TypeError('用户类型不正确, session.user_type 应该为 {} 而不是 {}'
                                .format(user_type, session.user_type))
            else:
                return func(session, *args, **kwargs)

        api_info = dict(url=url, method=method.lower(), user_type=user_type, func=registered_api_wrapper)
        if func.func_name in g.registered_api:
            raise NameError('{} 已注册过, 请确认 api 是否有重名'.format(func.func_name))
        g.registered_api[func.func_name] = api_info
        return registered_api_wrapper

    return _register_dec


def cache_api(duration=None, is_public=False):
    def _cache_dec(func):
        @wraps(func)
        def cached_api_wrapper(session, *args, **kwargs):
            if not g.current_cache_manager:
                logger.warning('当前没有缓存管理对象, 建议声明一个缓存管理对象')
                rv = func(session, *args, **kwargs)
            else:
                cache_md5 = cal_cache_md5(func, session, is_public, *args, **kwargs)
                rv = g.current_cache_manager.get(cache_md5)
                if not rv:
                    rv = func(session, *args, **kwargs)
                    g.current_cache_manager.set(cache_md5, value=rv, duration=duration)
            return rv

        return cached_api_wrapper

    return _cache_dec
