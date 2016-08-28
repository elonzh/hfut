# -*- coding:utf-8 -*-
"""
http://docs.pytest.org/en/latest/writing_plugins.html#conftest-py-local-per-directory-plugins
"""
from __future__ import unicode_literals

import csv
import os

import pytest

from hfut import StudentSession

base_dir = os.path.dirname(__file__)


def load_sessions():
    with open(os.path.join(base_dir, 'test_accounts.csv')) as fp:
        sessions = [StudentSession(account, password, campus) for account, password, campus in csv.reader(fp)]
    return sessions


@pytest.fixture(params=load_sessions())
def session(request):
    return request.param
