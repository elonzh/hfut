# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import pytest

from tests import TestBase

from hfut_stu_lib import StudentSession

pytest_args = [
    '--cov-config', '.coveragerc',
    '--cov-report', 'html',
    '--cov=hfut_stu_lib', 'tests/',
    '--doctest-modules'
]

TestBase.session = StudentSession(2013217413, 'fuckyou')
pytest.main(pytest_args)

TestBase.session = StudentSession(2013211263, '2013cym', is_hefei=True)
pytest.main(pytest_args)
