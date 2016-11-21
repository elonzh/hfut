# -*- coding:utf-8 -*-
"""
http://docs.pytest.org/en/latest/fixture.html
http://docs.pytest.org/en/latest/writing_plugins.html#conftest-py-local-per-directory-plugins
"""
from __future__ import unicode_literals

import csv
import os

import pytest

from hfut import Student, ENV

base_dir = os.path.dirname(__file__)


def load_shortcuts():
    with open(os.path.join(base_dir, 'test_accounts.csv')) as fp:
        for account, password, campus in csv.reader(fp):
            yield Student(account, password, campus)


@pytest.fixture(params=load_shortcuts())
def shortcuts(request):
    return request.param


@pytest.fixture(scope='class', params=['html.parser', 'lxml'])
def features(request):
    ENV['SOUP_FEATURES'] = request.param
