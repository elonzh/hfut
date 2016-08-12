# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from bs4 import BeautifulSoup

from hfut import parser, BaseSession


class TestParser(object):
    def test_parse_tr_strs(self):
        single_tag = "<tr><td>Fuck!</td></tr>"
        assert parser.parse_tr_strs([BeautifulSoup(single_tag, BaseSession.html_parser).tr]) == [['Fuck!']]
        wrong_tag = "<tr><td><font>Fuck!<font/><font>You!<font/></td></tr>"
        assert parser.parse_tr_strs([BeautifulSoup(wrong_tag, BaseSession.html_parser).tr]) == [['Fuck!You!']]
