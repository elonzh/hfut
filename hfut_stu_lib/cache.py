# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import inspect
import cPickle
import time
from hashlib import md5

try:
    import anydbm as dbm

    assert dbm
except ImportError:
    import dbm


class MemoryCache(object):
    def __init__(self, default_duration=259200):
        self.default_duration = default_duration
        self.data_container = {}

    def get(self, args_md5):
        data = self.data_container.get(args_md5)
        rv = None
        if data:
            if data['expire_time'] > time.time():
                rv = data['value']
            else:
                del self.data_container[args_md5]
        return rv

    def set(self, args_md5, value, duration=None):
        duration = duration or self.default_duration
        expire_time = time.time() + duration
        data = dict(value=value, expire_time=expire_time)
        self.data_container[args_md5] = data

    def delete(self, args_md5):
        del self.data_container[args_md5]

    def cal_args_md5(self, func_name, is_public, *args, **kwargs):
        argsspec = inspect.getcallargs(func, self, *args, **kwargs)
        argsspec.pop('self')
        if not is_public:
            argsspec[self.stu_id] = self.stu_id
        args_md5 = md5(cPickle.dumps(argsspec)).hexdigest()
        return args_md5

    def cache(self, duration=None, is_public=False):
        inst_proxy = self

        def _dec(func):
            def _wrapper(self, *args, **kwargs):
                argsspec = inspect.getcallargs(func, self, *args, **kwargs)
                argsspec.pop('self')
                if not is_public:
                    argsspec[self.stu_id] = self.stu_id
                args_md5 = md5(cPickle.dumps(argsspec)).hexdigest()

                rv = inst_proxy.get(args_md5)
                if not rv:
                    print '没有触发缓存'
                    rv = func.__get__(self, type(self))(*args, **kwargs)
                    inst_proxy.set(args_md5, value=rv, duration=duration)
                return rv

            return _wrapper

        return _dec


class FileCache(MemoryCache):
    def __init__(self, filename='hfut_stu_lib_cache', default_duration=259200):
        super(FileCache, self).__init__(default_duration)
        self.data_container = dbm.open(filename, 'c')


if __name__ == '__main__':
    c = FileCache()
    from lib import StuLib

    stu = StuLib(2013217413, '1234567')
    print stu.get_stu_info()
