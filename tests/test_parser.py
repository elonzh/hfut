# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from bs4 import BeautifulSoup

from hfut import parser, HTML_PARSER
from . import TestBase


class TestParser(TestBase):
    def test_parse_tr_strs(self):
        single_tag = "<tr><td>Fuck!</td></tr>"
        assert parser.parse_tr_strs([BeautifulSoup(single_tag, HTML_PARSER).tr]) == [['Fuck!']]
        wrong_tag = "<tr><td><font>Fuck!<font/><font>You!<font/></td></tr>"
        assert parser.parse_tr_strs([BeautifulSoup(wrong_tag, HTML_PARSER).tr]) == [['Fuck!You!']]

    def test_dict_list_2_matrix(self):
        assert parser.dict_list_2_matrix([{'a': 1, 'b': 2}, {'a': 3, 'b': 4}], ('a', 'b')) == [[1, 2], [3, 4]]
