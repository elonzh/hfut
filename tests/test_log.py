# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import requests

from hfut import log
from . import TestBase


class TestLog(TestBase):
    def test_report_response(self):
        response = requests.get('http://httpbin.org/redirect/3', params={'a': 1}, data={'body': '牛逼'})
        log.report_response(response)
