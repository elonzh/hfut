# -*- coding:utf-8 -*-
from __future__ import unicode_literals, division

import six
from bs4.element import Tag

from .log import logger


def parse_tr_strs(trs):
    """
    将没有值但有必须要的单元格的值设置为 None
    将 <tr> 标签数组内的单元格文字解析出来并返回一个二维列表
    :param trs: <tr> 标签数组, 为 BeautifulSoup 节点对象
    :return: 二维列表
    """
    if isinstance(trs, Tag):
        trs = [trs]
    tr_strs = []
    for tr in trs:
        strs = []
        for td in tr.find_all('td'):
            # 使用 stripped_strings 防止 td 中还有标签
            # 如: 不及格课程会有一个<font>标签导致tds[i].string为None
            # <FONT COLOR=#FF0000>37    </FONT></TD>
            # stripped_strings 是一个生成器, 没有长度
            # 生成器迭代一次就没有了, 需要转换为 tuple 或 list 进行保存
            s_list = tuple(td.stripped_strings)
            l = len(s_list)
            if l == 1:
                strs.append(s_list[0])
            elif l == 0:
                strs.append(None)
            else:
                msg = 'td标签中含有多个字符串\n{:s}'.format(td)
                logger.error(s_list)
                raise ValueError(msg)
        tr_strs.append(strs)
    return tr_strs if len(tr_strs) > 1 else tr_strs[0]


def flatten_list(multiply_list):
    """
    碾平 list
    >>> a = [1, 2, [3, 4], [[5, 6], [7, 8]]]
    >>> flatten_list(a)
    [1, 2, 3, 4, 5, 6, 7, 8]

    :param multiply_list: 混淆的多层列表
    :return: 单层的 list
    """
    if isinstance(multiply_list, list):
        return [rv for l in multiply_list for rv in flatten_list(l)]
    else:
        return [multiply_list]


def dict_list_2_tuple_set(dict_list_or_tuple_set, reverse=False):
    if reverse:
        return [dict(l) for l in dict_list_or_tuple_set]
    return {tuple(six.iteritems(d)) for d in dict_list_or_tuple_set}
