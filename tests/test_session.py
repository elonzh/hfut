# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import random

import pytest
from requests import HTTPError

from hfut import ENV, XC
from hfut.session import BaseSession
from . import TestBase


class TestSession(TestBase):
    def test_raise_for_status(self):
        assert ENV['RAISE_FOR_STATUS'] is False
        s = BaseSession(XC)
        s.get('http://httpbin.org/status/500')
        ENV['RAISE_FOR_STATUS'] = True
        with pytest.raises(HTTPError):
            s.get('http://httpbin.org/status/500')
        ENV['RAISE_FOR_STATUS'] = False

    def test_max_histories(self):
        origin = ENV['MAX_HISTORIES']
        s = BaseSession(XC)
        assert s.histories.maxlen == origin
        new = random.randint[1, 9]
        ENV['MAX_HISTORIES'] = new
        s = BaseSession(XC)
        assert s.histories.maxlen == new
        ENV['MAX_HISTORIES'] = origin
