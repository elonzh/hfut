# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import six


class TestBase(object):
    def assert_every_keys(self, seq, keys):
        keys.sort()
        for v in seq:
            assert sorted(six.iterkeys(v)), keys

    def assert_dict_keys(self, d, keys):
        keys.sort()
        assert sorted(six.iterkeys(d)) == keys
