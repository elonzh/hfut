# -*- coding:utf-8 -*-
"""
供直接调用的接口,所有接口使用 register_api 注册,并且至少有一个参数并且第一个参数为 auth_session, 返回结果类型由各个接口决定
"""
from __future__ import unicode_literals, print_function, division

import re

import six

from .api_request_builder import (GetClassStudent, GetClassInfo, SearchLessons, GetTeachingPlan, GetTeacherInfo,
                                  GetLessonClasses, GetCode, GetStuInfo, GetStuGrades, GetStuTimetable, GetStuFeeds,
                                  ChangePassword, SetTelephone, GetOptionalLessons, GetSelectedLessons, SelectLesson,
                                  DeleteLesson)
from .core import register_api, unfinished, unstable
from .logger import hfut_stu_lib_logger

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
def is_lesson_selected(auth_session, kcdm):
    """
    检查课程是否被选
    :param auth_session: AuthSession 对象
    :param kcdm:课程代码
    :return:已选返回True,未选返回False
    """
    selected_lessons = get_selected_lessons(auth_session)
    for lesson in selected_lessons:
        if kcdm.upper() == lesson['课程代码']:
            return True
    return False


# todo: 提交前判断人数
@register_api
def select_lesson(auth_session, kvs):
    """
    提交选课
    :param auth_session: AuthSession 对象
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
            if is_lesson_selected(auth_session, kcdm):
                hfut_stu_lib_logger.warning('课程 %s 你已经选过了', kcdm)
            else:
                if not jxbhs:
                    if is_lesson_selected(auth_session, kcdm):
                        hfut_stu_lib_logger.warning('你已经选了课程 %s, 如果你要选课的话, 请勿选取此课程代码', kcdm)
                    teaching_classes = get_lesson_classes(auth_session, kcdm)
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
    selected_lessons = get_selected_lessons(auth_session)
    for lesson in selected_lessons:
        kcdms_data.append(lesson['课程代码'])
        jxbhs_data.append(lesson['教学班号'])

    return auth_session.api_request(SelectLesson(auth_session.account, kcdms_data, jxbhs_data).gen_api_req_obj()).data


@register_api
def delete_lesson(auth_session, kcdms):
    # 对参数进行预处理
    kcdms = set(kcdms)
    kcdms = [v.upper() for v in kcdms]

    kcdms_data = []
    jxbhs_data = []
    selected_lessons = get_selected_lessons(auth_session)
    for lesson in selected_lessons:
        if lesson['课程代码'] not in kcdms:
            kcdms_data.append(lesson['课程代码'])
            jxbhs_data.append(lesson['教学班号'])
    return auth_session.api_request(DeleteLesson(auth_session.account, kcdms_data, jxbhs_data).gen_api_req_obj()).data
