# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import csv

import pytest

from hfut import StudentSession
from tests import TestBase

# http://docs.pytest.org/en/latest/usage.html
pytest_args = [
    '--cov-config', '.coveragerc',
    # '--cov-report', 'html',
    '--cov-report', 'term-missing',
    '--cov=hfut', 'tests/',
    '--doctest-modules',
    # '--pdb'
]

with open('test_accounts.csv') as fp:
    for account, password, campus in csv.reader(fp):
        start_msg = '使用 %s：%s 进行测试' % (campus, account)
        print(start_msg.center(72, '='))
        TestBase.session = StudentSession(account, password, campus)
        pytest.main(pytest_args)
