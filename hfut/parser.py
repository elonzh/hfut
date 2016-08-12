# -*- coding:utf-8 -*-
"""
页面解析相关的函数,如果你想自己编写接口可能用得到
"""
from __future__ import unicode_literals, division

import re
from pprint import pformat

import six

from .log import logger


def safe_zip(iter1, iter2, iter1_len=None, iter2_len=None):
    iter1 = tuple(iter1)
    iter2 = tuple(iter2)
    logger.debug('%s 与 %s 将要被 zip', iter1, iter2)
    if iter1_len and iter2_len:
        assert len(iter1) == iter1_len
        assert len(iter2) == iter2_len
    else:
        equal_len = iter1_len or iter2_len or len(iter1)
        assert len(iter1) == equal_len
        assert len(iter2) == equal_len
    return zip(iter1, iter2)


def parse_tr_strs(trs):
    """
    将没有值但有必须要的单元格的值设置为 None
    将 <tr> 标签数组内的单元格文字解析出来并返回一个二维列表

    :param trs: <tr> 标签或标签数组, 为 :class:`bs4.element.Tag` 对象
    :return: 二维列表
    """
    tr_strs = []
    for tr in trs:
        strs = []
        for td in tr.find_all('td'):
            text = td.get_text(strip=True)
            strs.append(text or None)
        tr_strs.append(strs)
    logger.debug('从行中解析出以下数据\n%s', pformat(tr_strs))
    return tr_strs


def flatten_list(multiply_list):
    """
    碾平 list::

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
    """

        >>> dict_list_2_tuple_set([{'a': 1, 'b': 2}, {'c': 3, 'd': 4}])
        {(('c', 3), ('d', 4)), (('a', 1), ('b', 2))}
        >>> dict_list_2_tuple_set({(('c', 3), ('d', 4)), (('a', 1), ('b', 2))}, reverse=True)
        [{'a': 1, 'b': 2}, {'c': 3, 'd': 4}]

    :param dict_list_or_tuple_set:
    :param reverse:
    :return:
    """
    if reverse:
        return [dict(l) for l in dict_list_or_tuple_set]
    return {tuple(six.iteritems(d)) for d in dict_list_or_tuple_set}


def parse_course(course_str):
    """
    解析课程表里的课程

    :param course_str: 形如 `单片机原理及应用[新安学堂434 (9-15周)]/数字图像处理及应用[新安学堂434 (1-7周)]/` 的课程表数据
    """
    # 解析课程单元格
    # 所有情况
    # 机械原理[一教416 (1-14周)]/
    # 程序与算法综合设计[不占用教室 (18周)]/
    # 财务管理[一教323 (11-17单周)]/
    # 财务管理[一教323 (10-16双周)]/
    # 形势与政策(4)[一教220 (2,4,6-7周)]/
    p = re.compile(r'(.+?)\[(.+?)\s+\(([\d,-单双]+?)周\)\]/')
    courses = p.findall(course_str)
    results = []
    for course in courses:
        d = {'课程名称': course[0], '课程地点': course[1]}
        # 解析上课周数
        week_str = course[2]
        l = week_str.split(',')
        weeks = []
        for v in l:
            m = re.match(r'(\d+)$', v) or re.match(r'(\d+)-(\d+)$', v) or re.match(r'(\d+)-(\d+)(单|双)$', v)
            g = m.groups()
            gl = len(g)
            if gl == 1:
                weeks.append(int(g[0]))
            elif gl == 2:
                weeks.extend([i for i in range(int(g[0]), int(g[1]) + 1)])
            else:
                weeks.extend([i for i in range(int(g[0]), int(g[1]) + 1, 2)])
        d['上课周数'] = weeks
        results.append(d)
    return results
