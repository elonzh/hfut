# -*- coding:utf-8 -*-
from __future__ import unicode_literals, print_function, division
from types import FunctionType
from collections.abc import Callable

# class API(object):
#     def __call__(self, a, *args, **kwargs):
#         print(self, a)
#
#
# class CM(type):
#     def __new__(mcs, name, bases, attrs):
#         attrs['f1'] = API.__call__
#         attrs['f2'] = API().__call__
#         return type.__new__(mcs, name, bases, attrs)
#
#
# class C(metaclass=CM):
#     pass

#
# if __name__ == '__main__':
#     c = C()
#     print(c.f1)
#     print(c.f1(1))
#     print(c.f2)
#     print(c.f2(2))

d = {}
print(list(map(lambda v: d.update([v]), zip(['a', 'b'], [1, 2]))))
print(d)
d.update([(1, 2)])
print(d)
