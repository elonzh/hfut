# -*- coding:utf-8 -*-
from __future__ import unicode_literals

"""
外网 222.195.8.201
机械工程系 172.18.6.93 172.18.6.94
信息工程系 172.18.6.95 172.18.6.96
化工与食品加工系 172.18.6.97
建筑工程系 172.18.6.98
商学系 172.18.6.99
:param func_name: 调用的方法名
:type func_name: unicode
:return: 相应功能的绝对请求地址
:rtype : unicode
"""
urls = {
    # 登陆页 POST 无需登陆
    'login': 'pass.asp',
    # 个人信息查询 GET
    'get_stu_info': 'student/asp/xsxxxxx.asp',
    # 成绩查询 GET
    'get_stu_grades': 'student/asp/Select_Success.asp',
    # 课表查询 GET
    'get_stu_timetable': 'student/asp/grkb1.asp',
    # 收费查询 GET
    'get_stu_feeds': 'student/asp/Xfsf_Count.asp',
    # 查询学期代码与专业代码 GET
    'get_code': 'student/asp/xqjh.asp',
    # 修改密码 POST
    'change_password': 'student/asp/amend_password_jg.asp',
    # 修改电话 POST
    'set_telephone': 'student/asp/amend_tel.asp',

    # 教学班查询 GET 无需登陆
    'get_class_students': 'student/asp/Jxbmdcx_1.asp',
    # 教学班详情 GET 无需登陆 选课时用得上
    'get_class_info': 'student/asp/xqkb1_1.asp',
    # 课程查询 POST 无需登录
    'search_lessons': 'student/asp/xqkb1.asp',
    # 计划查询 POST 无需登陆
    'get_teaching_plan': 'student/asp/xqkb2.asp',
    # 教师信息 GET 无需登陆
    'get_teacher_info': 'teacher/asp/teacher_info.asp',

    # 查询指定学期课程开课班级 GET
    # '': 'student/asp/xqkb2_1.asp',

    # ========== 选课功能相关 ==========
    # 可选课程  GET 第一轮
    'get_optional_lessons': 'student/asp/select_topLeft.asp',
    # 可选课程  GET 第二,三轮 结果与第一轮一致
    # 'get_optional_lessons': 'student/asp/select_topLeft_f3.asp',

    # 教学班级 GET 无需登录
    'get_lesson_classes': 'student/asp/select_topRight.asp',
    # 教学班级 GET 无需登录 有课程容量时间等信息
    # 'get_lesson_classes': 'student/asp/select_topRight_f3.asp',

    # 已选课程 GET
    'get_selected_lessons': 'student/asp/select_down_f3.asp',
    # 已选课程 第二,三轮 参数与结果与第一轮一致
    # 'get_selected_lessons': 'student/asp/select_downRight.asp',

    # 提交选课 POST
    # 'select_lesson': 'student/asp/selectKC_submit.asp',
    'select_lesson': 'student/asp/selectKC_submit_f3.asp',
}
