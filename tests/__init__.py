# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import six
import logging

from hfut_stu_lib import logger, GuestSession, StudentSession

logger.setLevel(logging.DEBUG)


class TestBase(object):
    session = None

    def assert_every_keys(self, seq, keys):
        keys.sort()
        for v in seq:
            assert sorted(six.iterkeys(v)), keys

    def assert_dict_keys(self, d, keys):
        keys.sort()
        assert sorted(six.iterkeys(d)) == keys
