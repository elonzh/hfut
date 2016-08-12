# -*- coding:utf-8 -*-
from __future__ import unicode_literals


class SystemLoginFailed(Exception):
    pass


class IPBanned(SystemLoginFailed):
    pass


class ValidationError(Exception):
    pass