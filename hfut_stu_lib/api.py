# -*- coding:utf-8 -*-
"""
供直接调用的接口,所有接口使用 register_api 注册,并且至少有一个参数并且第一个参数为 auth_session, 返回结果类型由各个接口决定
"""
from __future__ import unicode_literals, print_function, division

import six
import json
import re

from .api_request_builder import (GetClassStudent, GetClassInfo, SearchLessons, GetTeachingPlan, GetTeacherInfo,
                                  GetLessonClasses, GetCode, GetStuInfo, GetStuGrades, GetStuTimetable, GetStuFeeds,
                                  ChangePassword, SetTelephone, GetOptionalLessons, GetSelectedLessons, ChangeLesson)
from .core import register_api, unfinished, unstable
from .parser import dict_list_2_tuple_set
from .log import logger

__all__ = ['get_class_students', 'get_class_info', 'search_lessons', 'get_teaching_plan', 'get_teacher_info',
           'get_lesson_classes'].extend(
    ['get_code', 'get_stu_info', 'get_stu_grades', 'get_stu_timetable', 'get_stu_feeds', 'change_password',
     'set_telephone', 'get_optional_lessons', 'get_selected_lessons', 'is_lesson_selected', 'select_lesson',
     'delete_lesson']
)


# ---------- GUEST ----------
@register_api
def get_class_students(auth_session, xqdm, kcdm, jxbh):
    return auth_session.api_request(GetClassStudent(xqdm, kcdm, jxbh).gen_api_req_obj()).data


@register_api
def get_class_info(auth_session, xqdm, kcdm, jxbh):
    return auth_session.api_request(GetClassInfo(xqdm, kcdm, jxbh).gen_api_req_obj()).data


@unfinished
@register_api
def search_lessons(auth_session, xqdm, kcdm=None, kcmc=None):
    return auth_session.api_request(SearchLessons(xqdm, kcdm, kcmc).gen_api_req_obj()).data


@register_api
def get_teaching_plan(auth_session, xqdm, kclxdm, ccjbyxzy):
    return auth_session.api_request(GetTeachingPlan(xqdm, kclxdm, ccjbyxzy).gen_api_req_obj()).data


@register_api
def get_teacher_info(auth_session, jsh):
    return auth_session.api_request(GetTeacherInfo(jsh).gen_api_req_obj()).data


@register_api
def get_lesson_classes(auth_session, kcdm):
    return auth_session.api_request(GetLessonClasses(kcdm).gen_api_req_obj()).data


# ---------- STUDENT ----------
@register_api
def get_code(auth_session):
    return auth_session.api_request(GetCode().gen_api_req_obj()).data


@register_api
def get_stu_info(auth_session):
    return auth_session.api_request(GetStuInfo().gen_api_req_obj()).data


@register_api
def get_stu_grades(auth_session):
    return auth_session.api_request(GetStuGrades().gen_api_req_obj()).data


@unstable
@register_api
def get_stu_timetable(auth_session):
    return auth_session.api_request(GetStuTimetable().gen_api_req_obj()).data


@register_api
def get_stu_feeds(auth_session):
    return auth_session.api_request(GetStuFeeds().gen_api_req_obj()).data


@register_api
def change_password(auth_session, oldpwd, newpwd, new2pwd):
    """
    修改密码
    :param auth_session: AuthSession 对象
    :param oldpwd: 旧密码
    :param newpwd: 新密码
    :param new2pwd: 重复新密码
    """
    p = re.compile(r'^[\da-z]{6,12}$')
    # 若不满足密码修改条件便不做请求
    if oldpwd != auth_session.password or newpwd != new2pwd or not p.match(newpwd):
        return False
    # 若新密码与原密码相同, 直接返回 True
    if newpwd == oldpwd:
        return True
    api_result = auth_session.api_request(ChangePassword(oldpwd, newpwd, new2pwd).gen_api_req_obj())
    if api_result.data is True:
        auth_session.password = newpwd
    return api_result.data


@register_api
def set_telephone(auth_session, tel):
    tel = six.text_type(tel)
    p = re.compile(r'^\d{11}$|^\d{4}-\d{7}$')
    if not p.match(tel):
        return False

    return auth_session.api_request(SetTelephone(tel).gen_api_req_obj()).data


# ========== 选课功能相关 ==========
@register_api
def get_optional_lessons(auth_session):
    return auth_session.api_request(GetOptionalLessons().gen_api_req_obj()).data


@register_api
def get_selected_lessons(auth_session):
    return auth_session.api_request(GetSelectedLessons().gen_api_req_obj()).data


@register_api
def change_lesson(auth_session, select_lessons=None, delete_lessons=None):
    """
    提交选课
    :param auth_session: AuthSession 对象
    :param select_lessons: 形如 {'kcdm': '9900039X', jxbhs: ['0001', '0002']} 的课程代码与教学班号列表, jxbhs 可以为空代表选择所有可选班级
    :param delete_lessons: 需要删除的课程代码列表
    :return:选课结果, 返回选中的课程教学班列表
    """
    if not (select_lessons or delete_lessons):
        raise ValueError('select_lessons, delete_lessons 参数不能都为空!')
    # 参数处理
    select_lessons = select_lessons or []
    delete_lessons = {l.upper() for l in (delete_lessons or [])}

    selected_lessons = get_selected_lessons(auth_session)
    selected_kcdms = {lesson['课程代码'] for lesson in selected_lessons}

    # 尝试删除没有被选中的课程会出错
    unselected = delete_lessons.difference(selected_kcdms)
    if unselected:
        msg = '无法删除没有被选的课程 {}'.format(unselected)
        logger.error(msg)
        raise ValueError(msg)

    # 要提交的 kcdm 数据
    kcdms_data = []
    # 要提交的 jxbh 数据
    jxbhs_data = []

    # 必须添加已选课程, 同时去掉要删除的课程
    for lesson in selected_lessons:
        if lesson['课程代码'] not in delete_lessons:
            kcdms_data.append(lesson['课程代码'])
            jxbhs_data.append(lesson['教学班号'])

    # 选课
    for kv in select_lessons:
        kcdm = kv['kcdm'].upper()
        jxbhs = set(kv['jxbhs']) if kv.get('jxbhs') else set()

        teaching_classes = get_lesson_classes(auth_session, kcdm)
        if teaching_classes is None:
            logger.warning('课程[%s]没有可选班级', kcdm)
            continue

        # 反正是统一提交, 不需要判断是否已满
        optional_jxbhs = {c['教学班号'] for c in teaching_classes['可选班级']}
        if jxbhs:
            wrong_jxbhs = jxbhs.difference(optional_jxbhs)
            if wrong_jxbhs:
                msg = '课程[{}]{}没有教学班号{}'.format(kcdm, teaching_classes['课程名称'], wrong_jxbhs)
                logger.error(msg)
                raise ValueError(msg)
        else:
            jxbhs = optional_jxbhs
        for jxbh in jxbhs:
            kcdms_data.append(kcdm)
            jxbhs_data.append(jxbh)

    result = auth_session.api_request(ChangeLesson(auth_session.account, kcdms_data, jxbhs_data).gen_api_req_obj())
    logger.debug(result)
    # 通过已选课程前后对比确定课程修改结果
    before_change = dict_list_2_tuple_set(selected_lessons)
    after_change = dict_list_2_tuple_set(get_selected_lessons(auth_session))
    deleted = before_change.difference(after_change)
    selected = after_change.difference(before_change)
    result = {'删除课程': dict_list_2_tuple_set(deleted, reverse=True) or None,
              '选中课程': dict_list_2_tuple_set(selected, reverse=True) or None}
    logger.debug(result)
    return result


# ---------- 不需要专门的请求 ----------
@register_api
def is_lesson_selected(auth_session, kcdms):
    """
    检查课程是否被选
    :param auth_session: AuthSession 对象
    :param kcdms: 课程代码列表
    :return: 已选返回True,未选返回False
    """
    selected_lessons = get_selected_lessons(auth_session)
    selected_kcdms = {lesson['课程代码'] for lesson in selected_lessons}
    result = [True if kcdm in selected_kcdms else False for kcdm in kcdms]
    return result[0] if len(result) == 1 else result


@register_api
def get_lessons_can_be_selected(auth_session, kcdms=None, dump_result=True, filename='可选课程.json'):
    kcdms = kcdms or [l['课程代码'] for l in get_optional_lessons(auth_session)]
    result = []
    for kcdm in kcdms:
        lesson_classes = get_lesson_classes(auth_session, kcdm)
        if lesson_classes is not None:
            lesson_classes['可选班级'] = [c for c in lesson_classes['可选班级'] if c['课程容量'] > c['选中人数']]
            if len(lesson_classes['可选班级']) > 0:
                result.append(lesson_classes)
    if dump_result:
        json.dump(result, open(filename, 'w', encoding='utf-8'), ensure_ascii=False)
        logger.debug('result dumped to %s', filename)
    return result
