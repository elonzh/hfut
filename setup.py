# -*- coding:utf-8 -*-
from __future__ import unicode_literals

from setuptools import setup, find_packages
import hfut_stu_lib

with open('README.md') as fp:
    long_description = fp.read()

setup(
    name='hfut_stu_lib',
    version=hfut_stu_lib.__version__,
    keywords=('hfut', 'spider', 'edu', 'student', 'interface'),
    description='Provided full-featured interfaces for the educational administration system of HFUT.',
    long_description=long_description,
    license='MIT License',
    install_requires=['requests', 'beautifulsoup4'],

    author='erliang',
    author_email='eviler_liang@foxmail.com',
    url='https://github.com/evilerliang/hfut-stu-lib',

    packages=find_packages(),
    platforms='any',
    test_suite='hfut_stu_lib.test',

    datafile=[('./', ['README.md', 'CHANGES.md', 'LICENSE'])],
)
