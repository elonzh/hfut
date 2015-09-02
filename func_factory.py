# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import sys

reload(sys)
sys.setdefaultencoding('utf-8')
import uniout
import requests
import chardet

from bs4 import BeautifulSoup, SoupStrainer
from pprint import pprint

from hfut_stu_lib.lib import StuLib
from hfut_stu_lib.core import get_tr_strs

stu = StuLib(2013217413, '1234567')
url = stu.get_url('teacher_info')

jsh = '12000198'
params = {'jsh': jsh}
session = requests.Session()

res = session.get(url, params=params)
page = res.text



