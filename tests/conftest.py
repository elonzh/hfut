# -*- coding:utf-8 -*-
"""
http://docs.pytest.org/en/latest/writing_plugins.html#conftest-py-local-per-directory-plugins
"""
from __future__ import unicode_literals

import csv
import os

import pytest

from hfut import Student

base_dir = os.path.dirname(__file__)


def load_shortcuts():
    with open(os.path.join(base_dir, 'test_accounts.csv')) as fp:
        shortcuts = [Student(account, password, campus) for account, password, campus in csv.reader(fp)]
    return shortcuts


@pytest.fixture(params=load_shortcuts())
def shortcuts(request):
    return request.param
