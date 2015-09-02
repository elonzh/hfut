# -*- coding:utf-8 -*-
from __future__ import unicode_literals

from setuptools import setup, find_packages

with open('README.md') as fp:
    long_description = fp.read()

setup(
    name='hfut_stu_lib',
    version='0.0.1',
    keywords=('hfut', 'spider', 'edu', 'student', 'interface'),
    description='Provided full-featured interfaces for the educational administration system of HeFei University of Technology.',
    long_description=long_description,
    license='MIT License',
    install_requires=['requests', 'beautifulsoup4'],

    author='erliang',
    author_email='eviler_liang@foxmail.com',
    url='https://github.com/evilerliang/hfut-stu-lib',

    packages=find_packages(),
    platforms='any',

)
