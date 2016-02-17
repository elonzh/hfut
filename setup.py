# -*- coding:utf-8 -*-
from __future__ import unicode_literals

from setuptools import setup, find_packages
import hfut_stu_lib

with open('README.rst', encoding='utf-8') as fp:
    long_description = fp.read()


with open('requirements.txt') as fp:
    install_requires = fp.read().split()

setup(
    name=hfut_stu_lib.__title__,
    version=hfut_stu_lib.__version__,
    keywords=('hfut', 'spider', 'edu', 'student', 'interface'),
    description='Provided full-featured interfaces for the educational administration system of HFUT.',
    long_description=long_description,
    license=hfut_stu_lib.__license__,
    install_requires=install_requires,

    author=hfut_stu_lib.__author__,
    author_email='eviler_liang@foxmail.com',
    url='https://github.com/evilerliang/hfut-stu-lib',

    packages=find_packages(),
    platforms='any',
    test_suite='hfut_stu_lib.test',

    data_files=[('', ['README.rst', 'CHANGES.md', 'LICENSE'])],
)
