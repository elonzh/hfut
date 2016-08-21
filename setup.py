# -*- coding:utf-8 -*-
from __future__ import unicode_literals

from setuptools import setup, find_packages

import hfut
with open('README.rst', 'rb') as readme_file:
    readme = readme_file.read().decode('utf-8')
with open('HISTORY.rst', 'rb') as history_file:
    history = history_file.read().decode('utf-8')
with open('requirements.txt', 'rb') as fp:
    install_requires = fp.read().decode('utf-8').split()

setup(
    name=hfut.__title__,
    version=hfut.__version__,
    keywords=('hfut', 'edu', 'student', 'interface'),
    description=hfut.__doc__,
    long_description=readme + '\n\n' + history,
    license=hfut.__license__,

    author=hfut.__author__,
    author_email=hfut.__author_email__,
    url=hfut.__url__,

    packages=find_packages(),
    platforms='any',

    install_requires=install_requires,
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
