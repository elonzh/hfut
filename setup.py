# -*- coding:utf-8 -*-
# 在 Python2 下使用 unicode_literals 会导致自定义命令出错
# from __future__ import unicode_literals
import hfut_stu_lib

from setuptools import setup, find_packages

# from setuptools.command.test import test as TestCommand

# class PyTest(TestCommand):
#     user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]
#
#     def initialize_options(self):
#         TestCommand.initialize_options(self)
#         self.pytest_args = [
#             '--cov-config', '.coveragerc',
#             '--cov-report', 'html',
#             '--cov=hfut_stu_lib', 'tests/',
#             '--doctest-modules'
#         ]
#
#     def run_tests(self):
#         # import here, cause outside the eggs aren't loaded
#         import pytest
#         errno = pytest.main(self.pytest_args)
#         sys.exit(errno)


with open('README.rst', 'rb') as fp:
    long_description = fp.read().decode('utf-8')

with open('requirements.txt') as fp:
    install_requires = fp.read().split()

# with open('dev-requirements.txt') as fp:
#     tests_require = fp.read().split()

setup(
    name=hfut_stu_lib.__title__,
    version=hfut_stu_lib.__version__,
    keywords=('hfut', 'edu', 'student', 'interface'),
    description=hfut_stu_lib.__doc__,
    long_description=long_description,
    license=hfut_stu_lib.__license__,

    author=hfut_stu_lib.__author__,
    author_email=hfut_stu_lib.__author_email__,
    url=hfut_stu_lib.__url__,

    packages=find_packages(),
    platforms='any',

    # setup_requires=['pytest-runner'],
    install_requires=install_requires,
    # tests_require=tests_require,
    # cmdclass={'test': PyTest},
    # test_suite='tests',

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
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
