# -*- coding:utf-8 -*-
from __future__ import unicode_literals

from setuptools import setup, find_packages
import hfut_stu_lib

with open('README.rst', 'rb') as fp:
    long_description = fp.read().decode('utf-8')


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
    url='https://github.com/er1iang/hfut-stu-lib',

    packages=find_packages(),
    platforms='any',
    test_suite='hfut_stu_lib.test',

    # data_files=[('', ['README.rst', 'CHANGES.md', 'LICENSE'])],
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 5 - Production/Stable',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: SDK',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
