# -*- coding:utf-8 -*-
from __future__ import unicode_literals


def parse_tr_strs(trs):
    """
    将没有值但有必须要的单元格的值设置为 None
    将 <tr> 标签数组内的单元格文字解析出来并返回一个二维列表
    :param trs: <tr> 标签数组, 为 BeautifulSoup 节点对象
    :return: 二维列表
    """
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
                print s_list
                raise ValueError(msg)
        tr_strs.append(strs)
    return tr_strs
