# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import os
import time
import cPickle

try:
    import dbm
except ImportError:
    import anydbm as dbm

from .core import g
from .logger import hfut_stu_lib_logger

__all__ = ['BaseCache', 'MemoryCache', 'FileCache']

DEFAULT_DURATION = 259200


class BaseCache(object):
    def __new__(cls, *args, **kwargs):
        if g.current_cache_manager:
            hfut_stu_lib_logger.warning('已存在缓存管理对象 {} 操作不会生效'.format(g.current_cache_manager))
        else:
            g.current_cache_manager = cls.self = object.__new__(cls)

        return g.current_cache_manager

    def get(self, cache_md5):
        raise NotImplementedError

    def set(self, cache_md5, value, duration=None):
        raise NotImplementedError

    def delete(self, cache_md5):
        raise NotImplementedError

    def drop(self):
        raise NotImplementedError


class MemoryCache(BaseCache):
    def __init__(self, default_duration=DEFAULT_DURATION):
        self.default_duration = default_duration
        self.data_container = {}

    def get(self, cache_md5):
        data = self.data_container.get(cache_md5)
        rv = None
        if data:
            if data['expire_time'] > time.time():
                rv = data['value']
            else:
                del self.data_container[cache_md5]
        return rv

    def set(self, cache_md5, value, duration=None):
        duration = duration or self.default_duration
        expire_time = time.time() + duration
        data = dict(value=value, expire_time=expire_time)
        self.data_container[cache_md5] = data

    def delete(self, cache_md5):
        del self.data_container[cache_md5]

    def drop(self):
        self.data_container = {}


class FileCache(BaseCache):
    def __init__(self, filename='hfut_stu_lib.cache', default_duration=DEFAULT_DURATION):
        self.filename = filename
        self.data_container = dbm.open(self.filename, 'c')
        self.default_duration = default_duration

    def get(self, cache_md5):
        try:
            data = self.data_container[cache_md5]
        except KeyError:
            data = None
        rv = None
        if data:
            data = cPickle.loads(data)
            if data['expire_time'] > time.time():
                rv = data['value']
            else:
                del self.data_container[cache_md5]
                self.save()
        return rv

    def set(self, cache_md5, value, duration=None):
        duration = duration or self.default_duration
        expire_time = time.time() + duration
        data = dict(value=value, expire_time=expire_time)

        self.data_container[cache_md5] = cPickle.dumps(data)
        self.save()

    def delete(self, cache_md5):
        del self.data_container[cache_md5]
        self.save()

    def drop(self):
        if os.path.isfile(self.filename):
            os.remove(self.filename)

    def save(self):
        self.data_container.close()
        self.data_container = dbm.open(self.filename, 'c')
