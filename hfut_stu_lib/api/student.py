# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import re
import urlparse

from bs4 import SoupStrainer, BeautifulSoup

from ..const import SITE_ENCODING, HOST_URL, STUDENT
from ..logger import hfut_stu_lib_logger
from ..core import unstable, register_api, cache_api
from ..parser import parse_tr_strs
from .guest import get_lesson_classes

__all__ = ['get_code', 'get_stu_info', 'get_stu_grades', 'get_stu_timetable', 'get_stu_feeds', 'change_password',
           'set_telephone', 'get_optional_lessons', 'get_selected_lessons', 'is_lesson_selected', 'select_lesson',
           'delete_lesson']


@register_api('student/asp/xqjh.asp', user_type=STUDENT)
@cache_api(duration=259200, is_public=True)
def get_code(session):
    """
    获取专业, 学期的代码和名称
    """
    res = session.catch_response(get_code.func_name)
    # res = session.catch_response('get_code')
    page = res.text

    ss = SoupStrainer('select')
    bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
    xqdm_options = bs.find('select', attrs={'name': 'xqdm'}).find_all('option')
    xqdm = [{'key': node['value'], 'name': node.string.strip()} for node in xqdm_options]
    ccjbyxzy_options = bs.find('select', attrs={'name': 'ccjbyxzy'}).find_all('option')
    ccjbyxzy = [{'key': node['value'], 'name': node.string.strip()} for node in ccjbyxzy_options]
    result = {'xqdm': xqdm, 'ccjbyxzy': ccjbyxzy}
    return result


@register_api('student/asp/xsxxxxx.asp', user_type=STUDENT)
@cache_api(duration=259200, is_public=False)
def get_stu_info(session):
    res = session.catch_response(get_stu_info.func_name)
    page = res.text
    ss = SoupStrainer('table')
    bs = BeautifulSoup(page, 'html.parser', parse_only=ss)

    key_trs = bs.find_all('tr', height='16', bgcolor='#A0AAB4')
    key_lines = parse_tr_strs(key_trs)
    value_trs = bs.find_all('tr', height='16', bgcolor='#D6D3CE')
    value_lines = parse_tr_strs(value_trs)

    assert len(key_lines) == len(value_lines) - 2

    stu_info = {}
    # 解析前面的两行, 将第一行合并到第二行后面,因为第一行最后一列为头像
    value_lines[1].extend(value_lines[0])
    kvs = []
    for cell in value_lines[1][:-1]:
        kv_tuple = (v.strip() for v in cell.split(':'))
        kvs.append(kv_tuple)
    stu_info.update(kvs)

    # 解析后面对应的信息
    for line in zip(key_lines, value_lines[2:]):
        stu_info.update(zip(line[0], line[1]))

    # 添加照片项
    url = 'student/photo/{:s}/{:d}.JPG'.format(unicode(session.account)[:4], session.account)
    stu_info['照片'] = urlparse.urljoin(HOST_URL, url)

    return stu_info


@register_api('student/asp/Select_Success.asp', user_type=STUDENT)
@cache_api(duration=259200, is_public=False)
def get_stu_grades(session):
    res = session.catch_response(get_stu_grades.func_name)
    page = res.text
    ss = SoupStrainer('table', width='582')
    bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
    trs = bs.find_all('tr')
    keys = tuple(trs[0].stripped_strings)
    # 不包括表头行和表底学分统计行
    values_list = parse_tr_strs(trs[1:-1])
    grades = []
    for values in values_list:
        grade = dict(zip(keys, values))
        grade['课程代码'] = grade['课程代码'].upper()
        grades.append(grade)
    return grades


@unstable
@register_api('student/asp/grkb1.asp', user_type=STUDENT)
@cache_api(duration=259200, is_public=False)
def get_stu_timetable(session, detail=False):
    res = session.catch_response(get_stu_timetable.func_name)
    page = res.text
    ss = SoupStrainer('table', width='840')
    bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
    trs = bs.find_all('tr')
    origin_list = parse_tr_strs(trs[1:])

    def parse_lesson(lesson):
        # todo:课程时间还有特殊情况, 例如形势政策, 应完善正则
        """
        解析课程单元格
        """
        if lesson is None:
            return None

        import re

        p = re.compile(r'(.+?)\[(.+?) \((\d{1,2})-(\d{1,2})(单|)周\)\]/')
        matched_results = p.findall(unicode(lesson))
        results = []
        for r in matched_results:
            d = {'课程名称': r[0],
                 '课程地点': r[1],
                 '起始周': r[2],
                 '结束周': r[3],
                 '单双周': r[4]}
            results.append(d)
        return results

    # 顺时针反转矩阵
    length = len(origin_list)
    width = len(origin_list[0])
    new_matrix = []
    if not detail:
        for i in xrange(width):
            newline = []
            for j in xrange(length):
                newline.append(origin_list[j][i])
            new_matrix.append(newline)
    else:
        for i in xrange(width):
            newline = []
            for j in xrange(length):
                newline.append(parse_lesson(origin_list[j][i]))
            new_matrix.append(newline)

    # 去除第一行的序号
    timetable = new_matrix[1:]
    return timetable


@register_api('student/asp/Xfsf_Count.asp', user_type=STUDENT)
@cache_api(duration=259200, is_public=False)
def get_stu_feeds(session):
    res = session.catch_response(get_stu_feeds.func_name)
    page = res.text
    ss = SoupStrainer('table', bgcolor='#000000')
    bs = BeautifulSoup(page, 'html.parser', parse_only=ss)

    keys = tuple(bs.table.thead.tr.stripped_strings)
    value_trs = bs.find_all('tr', bgcolor='#D6D3CE')
    value_list = [tr.stripped_strings for tr in value_trs]
    feeds = []
    for values in value_list:
        feed = dict(zip(keys, values))
        feed['课程代码'] = feed['课程代码'].upper()
        feeds.append(feed)
    return feeds


@register_api('student/asp/amend_password_jg.asp', method='post', user_type=STUDENT)
def change_password(session, oldpwd, newpwd, new2pwd):
    """
    修改密码
    :param oldpwd: 旧密码
    :param newpwd: 新密码
    :param new2pwd: 重复新密码
    """
    p = re.compile(r'^[\da-z]{6,12}$')
    # 若不满足密码修改条件便不做请求
    if oldpwd != session.password or newpwd != new2pwd or not p.match(newpwd):
        return False
    # 若新密码与原密码相同, 直接返回 True
    if newpwd == oldpwd:
        return True

    data = {'oldpwd': oldpwd,
            'newpwd': newpwd,
            'new2pwd': new2pwd}

    res = session.catch_response(change_password.func_name, data=data)
    page = res.text
    ss = SoupStrainer('table', width='580', border='0', cellspacing='1', bgcolor='#000000')
    bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
    res = bs.text.strip()
    if res == '密码修改成功！':
        # todo: 改变了作用域此处无法传递回原对象，需要修改
        session.password = newpwd
        return True
    else:
        hfut_stu_lib_logger.warning('密码修改失败\noldpwd: {:s}\nnewpwd: {:s}\nnew2pwd: {:s}\ntext: {:s}'.format(
            oldpwd, newpwd, new2pwd, res
        ))
        return False


@register_api('student/asp/amend_tel.asp', method='post', user_type=STUDENT)
def set_telephone(session, tel):
    """
    更新电话
    :param tel: 电话号码
    """
    tel = unicode(tel)
    p = re.compile(r'^\d{11}$|^\d{4}-\d{7}$')
    if not p.match(tel):
        return False

    data = {'tel': tel}
    res = session.catch_response(set_telephone.func_name, data=data)
    page = res.text
    ss = SoupStrainer('input', attrs={'name': 'tel'})
    bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
    return bs.input['value'] == tel


# ========== 选课功能相关 ==========
@register_api('student/asp/select_topLeft.asp', user_type=STUDENT)
def get_optional_lessons(session, kclx='x'):
    """
    获取可选课程, 并不判断是否选满
    :param kclx: 课程类型参数,只有三个值,{x:全校公选课, b:全校必修课, jh:本专业计划},默认为'x'
    """
    if kclx in ('x', 'b', 'jh'):
        params = {'kclx': kclx}
        res = session.catch_response(get_optional_lessons.func_name,
                                     params=params, allow_redirects=False)
        page = res.text
        ss = SoupStrainer('table', id='KCTable')
        bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
        lessons = []
        trs = bs.find_all('tr')
        value_list = [tuple(tr.stripped_strings) for tr in trs[:-1]]
        for values in value_list:
            lesson = {'课程代码': values[0].upper(),
                      '课程名称': values[1],
                      '课程类型': values[2],
                      '开课院系': values[3],
                      '学分': values[4]}
            lessons.append(lesson)
        return lessons
    else:
        raise ValueError('kclx 参数不正确!')


@register_api('student/asp/select_down_f3.asp', user_type=STUDENT)
def get_selected_lessons(session):
    """
    获取已选课程
    """
    res = session.catch_response(get_selected_lessons.func_name, allow_redirects=False)
    page = res.text
    ss = SoupStrainer('table', id='TableXKJG')
    bs = BeautifulSoup(page, 'html.parser', parse_only=ss)

    lessons = []
    keys = tuple(bs.find('tr', bgcolor='#296DBD').stripped_strings)
    value_list = [tr.stripped_strings for tr in bs.find_all('tr', bgcolor='#D6D3CE')]
    for values in value_list:
        lesson = dict(zip(keys, values))
        lesson['课程代码'] = lesson['课程代码'].upper()
        lessons.append(lesson)
    return lessons


@register_api('', user_type=STUDENT)
def is_lesson_selected(session, kcdm):
    """
    检查课程是否被选
    :param kcdm:课程代码
    :return:已选返回True,未选返回False
    """
    selected_lessons = get_selected_lessons(session)
    for lesson in selected_lessons:
        if kcdm.upper() == lesson['课程代码']:
            return True
    return False


@register_api('student/asp/selectKC_submit_f3.asp', method='post', user_type=STUDENT)
def select_lesson(session, kvs):
    """
    提交选课
    :param kvs:课程代码
    :return:选课结果, 返回选中的课程教学班列表
    """
    # 参数中的课程代码, 用于检查参数
    kcdms = set()
    # 要提交的 kcdm 数据
    kcdms_data = []
    # 要提交的 jxbh 数据
    jxbhs_data = []
    # 参数处理
    for kv in kvs:
        kcdm = kv['kcdm'].upper()
        jxbhs = kv['jxbhs']
        if kcdm not in kcdms:
            kcdms.add(kcdm)
            if is_lesson_selected(session, kcdm):
                hfut_stu_lib_logger.warning('课程 {:s} 你已经选过了'.format(kcdm))
            else:
                if not jxbhs:
                    if is_lesson_selected(session, kcdm):
                        hfut_stu_lib_logger.warning('你已经选了课程 {:s}, 如果你要选课的话, 请勿选取此课程代码'.format(kcdm))
                    teaching_classes = get_lesson_classes(kcdm)
                    for klass in teaching_classes:
                        kcdms_data.append(kcdm)
                        jxbhs_data.append(klass['教学班号'])
                else:
                    for jxbh in jxbhs:
                        kcdms_data.append(kcdm)
                        jxbhs_data.append(jxbh)
        else:
            raise ValueError('你有多个 kcdm={:s} 的字典, 请检查你的参数'.format(kcdm))

    # 必须添加已选课程
    selected_lessons = get_selected_lessons(session)
    for lesson in selected_lessons:
        kcdms_data.append(lesson['课程代码'])
        jxbhs_data.append(lesson['教学班号'])

    data = {'xh': session.account, 'kcdm': kcdms_data, 'jxbh': jxbhs_data}
    res = session.catch_response(select_lesson.func_name, data=data, allow_redirects=False)
    if res.status_code == 302:
        msg = '提交选课失败, 可能是身份验证过期或选课系统已关闭'
        hfut_stu_lib_logger.error(msg)
        raise ValueError(msg)
    else:
        page = res.text
        # 当选择同意课程的多个教学班时, 若已选中某个教学班, 再选择其他班数据库会出错,
        # 其他一些不可预料的原因也会导致数据库出错
        p = re.compile(r'(成功提交选课数据|容量已满,请选择其他教学班).+?'
                       r'课程代码：\s*([\dbBxX]+)[\s;&nbsp]*教学班号：\s*(\d{4})', re.DOTALL)
        r = p.findall(page)
        if not r:
            hfut_stu_lib_logger.warning('正则没有匹配到结果，可能出现了一些状况\n{:s}'.format(page))
            return None
        results = []
        for g in r:
            hfut_stu_lib_logger.info(' '.join(g))
            msg, kcdm, jxbh = g
            if msg == '成功提交选课数据':
                result = {'课程代码': kcdm.upper(), '教学班号': jxbh}
                results.append(result)
        return results


@register_api('student/asp/selectKC_submit_f3.asp', method='post', user_type=STUDENT)
def delete_lesson(session, kcdms):
    # 对参数进行预处理
    kcdms = set(kcdms)
    kcdms = map(lambda v: v.upper(), kcdms)

    kcdms_data = []
    jxbhs_data = []
    selected_lessons = get_selected_lessons(session)
    for lesson in selected_lessons:
        if lesson['课程代码'] not in kcdms:
            kcdms_data.append(lesson['课程代码'])
            jxbhs_data.append(lesson['教学班号'])

    data = {'xh': session.account, 'kcdm': kcdms_data, 'jxbh': jxbhs_data}
    res = session.catch_response(select_lesson.func_name, data=data, allow_redirects=False)
    if res.status_code == 302:
        msg = '课程删除失败, 可能是身份验证过期或选课系统已关闭'
        hfut_stu_lib_logger.error(msg)
        raise ValueError(msg)
    else:
        page = res.content.decode(SITE_ENCODING)
        # 当选择同意课程的多个教学班时, 若已选中某个教学班, 再选择其他班数据库会出错,
        # 其他一些不可预料的原因也会导致数据库出错
        p = re.compile(r'(已成功删除下列选课数据).+?课程代码：\s*([\dbBxX]+)[\s;&nbsp]*教学班号：\s*(\d{4})',
                       re.DOTALL)
        r = p.findall(page)
        if not r:
            hfut_stu_lib_logger.warning('正则没有匹配到结果，可能出现了一些状况\n{:s}'.format(page))
            return None
        results = []
        for g in r:
            hfut_stu_lib_logger.info(' '.join(g))
            msg, kcdm, jxbh = g
            result = {'课程代码': kcdm.upper(), '教学班号': jxbh}
            results.append(result)
        return results
