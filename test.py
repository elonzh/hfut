# -*- coding:utf-8 -*-
from __future__ import unicode_literals

from unittest import TestCase, main

from lib import StuLib


class StuLibTest(TestCase):
    def setUp(self):
        self.stu = StuLib(2013217413, '1234567')

    def tearDown(self):
        pass

    def test_login(self):
        self.stu.login()


if __name__ == '__main__':
    main()
