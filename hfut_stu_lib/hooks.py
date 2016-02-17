# -*- coding:utf-8 -*-
from __future__ import unicode_literals, print_function, division

from .const import SITE_ENCODING


def response_encoding(response, **kwargs):
    response.encoding = SITE_ENCODING
    return response
