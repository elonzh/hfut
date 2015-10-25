# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import re

from bs4 import SoupStrainer, BeautifulSoup

from ..logger import hfut_stu_lib_logger
from ..core import unfinished, regist_api
from ..parser import parse_tr_strs

__all__ = ['get_class_students', 'get_class_info', 'search_lessons', 'get_teaching_plan', 'get_teacher_info',
           'get_lesson_classes']


@regist_api('student/asp/Jxbmdcx_1.asp')
def get_class_students(session, xqdm, kcdm, jxbh):
    """
    教学班查询
    :param xqdm: 学期代码
    :param kcdm: 课程代码
    :param jxbh: 教学班号
    """
    params = {'xqdm': xqdm,
              'kcdm': kcdm,
              'jxbh': jxbh}
    res = session.catch_response(get_class_students.func_name, params=params)
    page = res.text
    # 狗日的网页代码写错了无法正确解析标签!
    term_p = r'\d{4}-\d{4}学年第(一|二)学期'
    term = re.search(term_p, page)
    class_name_p = r'[\u4e00-\u9fa5\w-]+\d{4}班'
    class_name = re.search(class_name_p, page)
    # 虽然 \S 能解决匹配失败中文的问题, 但是最后的结果还是乱码的
    stu_p = r'>\s*?(\d{1,3})\s*?</.*?>\s*?(\d{10})\s*?</.*?>\s*?([\u4e00-\u9fa5*]+)\s*?</'
    stus = re.findall(stu_p, page, re.DOTALL)
    if term and class_name and stus:
        stus = map(lambda v: {'序号': v[0], '学号': v[1], '姓名': v[2]}, stus)
        return {'学期': term.group(), '班级名称': class_name.group(), '学生': stus}
    elif page.find('无此教学班') != -1:
        hfut_stu_lib_logger.warning('无此教学班, 请检查你的参数')
        return None
    else:
        msg = '\n'.join(['没有匹配到信息, 可能出现了一些问题', page])
        hfut_stu_lib_logger.error(msg)
        raise ValueError(msg)


@regist_api('student/asp/xqkb1_1.asp')
def get_class_info(session, xqdm, kcdm, jxbh):
    """
    获取教学班详情
    :param xqdm: 学期代码
    :param kcdm: 课程代码
    :param jxbh: 教学班号
    """
    params = {'xqdm': xqdm,
              'kcdm': kcdm,
              'jxbh': jxbh}
    res = session.catch_response(get_class_info.func_name, params=params)
    page = res.text
    ss = SoupStrainer('table', width='600')
    bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
    # 有三行
    key_list = [tr.stripped_strings for tr in bs.find_all('tr', bgcolor='#B4B9B9')]
    assert len(key_list) == 3
    # 有六行, 前三行与 key_list 对应, 后四行是单行属性, 键与值在同一行
    trs = bs.find_all('tr', bgcolor='#D6D3CE')
    # 最后的 备注, 禁选范围 两行外面包裹了一个 'tr' bgcolor='#D6D3CE' 时间地点 ......
    tr4 = trs[4]
    special_kv = tuple(tr4.stripped_strings)[:2]
    trs.remove(tr4)

    value_list = parse_tr_strs(trs)
    assert len(value_list) == 6

    class_info = {}
    # 前三行, 注意 value_list 第三行是有两个单元格为 None,
    # 但key_list 用的是 tr.stripped_strings, zip 时消去了这一部分
    map(lambda seq: class_info.update(dict(zip(seq[0], seq[1]))), zip(key_list, value_list))
    # 后四行
    class_info.update(value_list[3:])
    class_info.update((special_kv,))
    return class_info


@unfinished
@regist_api('student/asp/xqkb1.asp', 'post')
def search_lessons(session, xqdm, kcdm=None, kcmc=None):
    """
    课程查询
    :param xqdm: 学期代码
    :param kcdm: 课程代码
    :param kcmc: 课程名称
    """
    # todo:完成课程查询, 使用 kcmc 无法查询成功, 可能是请求编码有问题
    if kcdm is None and kcmc is None:
        raise ValueError('kcdm 和 kcdm 参数必须至少存在一个')
    data = {'xqdm': xqdm,
            'kcdm': kcdm,
            'kcmc': kcmc}
    res = session.catch_response(search_lessons.func_name, data=data)

    page = res.text
    ss = SoupStrainer('table', width='650')
    bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
    term = bs.find('font', size='3', string=re.compile(r'\d{4}-\d{4}学年第(一|二)学期'))
    title = bs.find('tr', bgcolor='#FB9E04')
    trs = bs.find_all('tr', bgcolor=re.compile(r'#D6D3CE|#B4B9B9'))
    if term and title and trs:
        lessons = []
        term = term.string.strip()
        keys = tuple(title.stripped_strings)
        value_list = [tr.stripped_strings for tr in trs]
        for values in value_list:
            lesson = dict(zip(keys, values))
            lesson['课程代码'] = lesson['课程代码'].upper()
            lessons.append(lesson)
        return {'学期': term, '课程': lessons}
    else:
        hfut_stu_lib_logger.warning('没有找到结果\n xqdm={:s}, kcdm={:s}, kcmc={:s}'.format(xqdm, kcdm, kcmc))
        return None


@regist_api('student/asp/xqkb2.asp', 'post')
def get_teaching_plan(session, xqdm, kclxdm, ccjbyxzy):
    """
    计划查询
    :param xqdm: 学期代码
    :param kclxdm: 课程类型代码 必修为 1, 任选为 3
    :param ccjbyxzy: 专业
    """
    data = {'xqdm': xqdm,
            'kclxdm': kclxdm,
            'ccjbyxzy': ccjbyxzy}
    res = session.catch_response(get_teaching_plan.func_name, data=data)
    page = res.text
    ss = SoupStrainer('table', width='650')
    bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
    trs = bs.find_all('tr')
    keys = tuple(trs[1].stripped_strings)
    value_list = [tr.stripped_strings for tr in trs[2:]]
    teaching_plan = []
    for values in value_list:
        plan = dict(zip(keys, values))
        plan['课程代码'] = plan['课程代码'].upper()
        teaching_plan.append(plan)
    return teaching_plan


@regist_api('teacher/asp/teacher_info.asp')
def get_teacher_info(session, jsh):
    """
    查询教师信息
    :param jsh:8位教师号
    """
    params = {'jsh': jsh}
    res = session.catch_response(get_teacher_info.func_name, params=params)
    page = res.text
    ss = SoupStrainer('table')
    bs = BeautifulSoup(page, 'html.parser', parse_only=ss)

    value_list = parse_tr_strs(bs.find_all('tr'))
    # 第一行最后有个照片项
    teacher_info = {'照片': value_list[0].pop()}
    # 第五行最后有两个空白
    value_list[4] = value_list[4][:2]
    # 第六行有两个 联系电话 键
    phone = value_list[5]
    teacher_info['联系电话'] = phone[1::2]
    value_list.remove(phone)
    # 解析其他项
    for v in value_list:
        for i in xrange(0, len(v), 2):
            teacher_info[v[i]] = v[i + 1]
    return teacher_info


@regist_api('student/asp/select_topRight.asp')
def get_lesson_classes(session, kcdm, detail=False):
    """
    获取选课系统中课程的可选教学班级
    :param kcdm:课程代码
    """
    params = {'kcdm': kcdm}
    res = session.catch_response(get_lesson_classes.func_name, params=params, allow_redirects=False)
    page = res.text
    ss = SoupStrainer('table', id='JXBTable')
    bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
    trs = bs.find_all('tr')

    lesson_classes = []
    for tr in trs:
        klass = {}
        tds = tr.find_all('td')
        assert len(tds) == 5
        klass['教学班号'] = tds[1].string.strip()
        klass['教师'] = tds[2].text.strip()
        klass['优选范围'] = tds[3].text.strip()

        if detail:
            href = tds[1].a['href']
            # 匹配当前的学期代码
            xqdm = re.search(r"(?<=,')\d{3}(?='\))", href).group()
            klass.update(get_class_info(xqdm, kcdm, klass['教学班号']))

        lesson_classes.append(klass)
    return lesson_classes
