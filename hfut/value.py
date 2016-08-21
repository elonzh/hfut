# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import re
from functools import wraps
import six

HF = 'HF'
XC = 'XC'
HOSTS = {HF: 'http://bkjw.hfut.edu.cn/', XC: 'http://222.195.8.201/'}

# https://docs.python.org/3/library/re.html
TERM_PATTERN = re.compile(r'(\d{4})(?:|学年)-\d{4}学年\s*第(一|二|二/三)学期(|/暑期)')
ACCOUNT_PATTERN = re.compile(r'^\d{10}$')
XC_PASSWORD_PATTERN = re.compile(r'^[\da-z]{6,12}$')
HF_PASSWORD_PATTERN = re.compile(r'^[^\s,;*_?@#$%&()+=><]{6,16}$')

ILLEGAL_CHARACTERS_PATTERN = re.compile(r'[,;*_?@#$%&()+=><]')


def validate_attrs(validators):
    # @wraps
    # AttributeError: 'mappingproxy' object has no attribute 'update'

    def wrapper(cls):
        for k, v in validators.items():
            if isinstance(v, six.text_type):
                validator = getattr(cls, v)
                if not (validator and callable(validator)):
                    raise ValueError('%s：%s 不是一个正确的验证器' % (k, v))
                validators[k] = validator
        if hasattr(cls, '_validators'):
            # 子类能够继承父类的属性验证器
            cls._validators.update(validators)
        else:
            cls._validators = validators

            def validate(self, name, value):
                if name in self._validators:
                    self._validators[name](self, value)
                super(cls, self).__setattr__(name, value)

            cls.__setattr__ = validate
        return cls

    return wrapper

# todo: 对请求参数中的非法字符进行检查, 避免登陆成功后却因输入非法字符导致 IP 被封禁
# inspect.getfullargspec(func)
# Deprecated since version 3.5: Use signature() and Signature Object,
#  which provide a better introspecting API for callables.
# def validate_args(validators):
#     def decorator(fn):
#         @wraps(fn)
#         def wrap(*args, **kwargs):
#             pass
#
#         return wrap
#
#     return decorator
