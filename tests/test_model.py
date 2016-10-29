# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import random

import pytest

from hfut import HF, XC
from . import TestBase


class TestGuest(TestBase):
    def test_get_class_students(self, shortcuts):
        keys = ['学期', '班级名称', '学生']
        # 电子电路课程设计A0001班
        kcdm = '0400073B'
        jxbh = '0001'
        res = shortcuts.get_class_students('025', kcdm, jxbh)
        assert res == {}
        res = shortcuts.get_class_students('026', kcdm, jxbh)
        self.assert_dict_keys(res, keys)
        if shortcuts.session.campus == HF:
            assert len(res['学生']) == 40
        else:
            assert len(res['学生']) == 45

        # 大学语文  0001班
        shortcuts.get_class_students('022', '5202012B', '0001')
        # 大学英语拓展（一）0001班
        shortcuts.get_class_students('029', '9900039X', '0001')

    def test_get_class_info(self, shortcuts):
        keys = ['时间地点', '开课单位', '禁选范围', '考核类型', '性别限制', '教学班号', '课程名称', '优选范围', '备注',
                '学分', '课程类型', '校区', '选中人数', '起止周']
        res = shortcuts.get_class_info('026', '0400073B', '0001')
        self.assert_dict_keys(res, keys)
        res = shortcuts.get_class_info('028', '0532142B', '0001')
        self.assert_dict_keys(res, keys)

    def test_search_course(self, shortcuts):
        keys = ['班级容量', '教学班号', '课程名称', '任课教师', '课程代码', '课程类型']
        with pytest.raises(ValueError):
            shortcuts.search_course('027')
        res = shortcuts.search_course('027', kcdm='1400011B')
        self.assert_every_keys(res, keys)
        res = shortcuts.search_course('027', kcmc='微波')
        assert len(res) == 1
        assert shortcuts.search_course('000', kcmc='臭傻逼') == []

    def test_get_teaching_plan(self, shortcuts):
        keys = ['开课单位', '学时', '课程名称', '课程代码', '学分']
        # 2013*微电子科学与工程 在 026 学期没有计划
        res = shortcuts.get_teaching_plan('026', 'b', '0120133226')
        assert res == []
        res = shortcuts.get_teaching_plan('028', 'x')
        self.assert_every_keys(res, keys)
        if shortcuts.session.campus == XC:
            assert len(res) == 33
        else:
            assert len(res) == 126

    def test_get_teacher_info(self, shortcuts):
        keys = ['教研室', '教学课程', '学历', '教龄', '教师寄语', '简 历', '照片', '科研方向', '出生', '姓名',
                '联系电话', '职称', '电子邮件', '性别', '学位', '院系']
        # 张燕子 在两个校区都有记录且教师号一致
        jsh = '12000199'
        res = shortcuts.get_teacher_info(jsh)
        self.assert_dict_keys(res, keys)

    def test_get_entire_curriculum(self, shortcuts):
        res = shortcuts.get_entire_curriculum('028')
        assert len(res['课表']) == 7
        for v in res['课表']:
            assert len(v) == 11
        res = shortcuts.get_entire_curriculum('000')
        assert res['起始周'] == res['结束周'] == 0


class TestStudent(TestBase):
    def test_is_expired(self, shortcuts):
        assert shortcuts.session.is_expired is False

    def test_get_code(self, shortcuts):
        shortcuts.get_code()

    def test_get_my_info(self, shortcuts):
        keys = ['婚姻状况', '毕业高中', '专业简称', '家庭地址', '能否选课', '政治面貌', '性别', '学院简称', '外语语种',
                '入学方式', '照片', '联系电话', '姓名', '入学时间', '籍贯', '民族', '学号', '家庭电话', '生源地',
                '出生日期', '学籍状态', '身份证号', '考生号', '班级简称', '注册状态']
        res = shortcuts.get_my_info()
        self.assert_dict_keys(res, keys)

    def test_get_my_achievements(self, shortcuts):
        keys = ['教学班号', '课程名称', '学期', '补考成绩', '课程代码', '学分', '成绩']
        res = shortcuts.get_my_achievements()
        self.assert_every_keys(res, keys)

    def test_get_my_curriculum(self, shortcuts):
        res = shortcuts.get_my_curriculum()
        assert len(res['课表']) == 7
        for v in res['课表']:
            assert len(v) == 11

    def test_get_my_fees(self, shortcuts):
        keys = ['教学班号', '课程名称', '学期', '收费(元)', '课程代码', '学分']
        res = shortcuts.get_my_fees()
        self.assert_every_keys(res, keys)

    def test_change_password(self, shortcuts):
        if shortcuts.session.campus == HF:
            with pytest.raises(ValueError):
                shortcuts.change_password('123456')
        else:
            password = shortcuts.session.password
            with pytest.raises(ValueError):
                # 新密码太短
                shortcuts.change_password('12345')
            with pytest.raises(ValueError):
                # 新密码太长
                shortcuts.change_password('1234567890123')
            with pytest.raises(ValueError):
                # 新密码与原密码相同
                shortcuts.change_password(password)
            # 新密码与原密码不同
            assert shortcuts.change_password('123456') is True
            assert shortcuts.session.password == '123456'
            # 改回原密码
            assert shortcuts.change_password(password) is True

    def test_set_telephone(self, shortcuts):
        with pytest.raises(ValueError):
            shortcuts.set_telephone('1234567')
        assert shortcuts.set_telephone('12345678901') is True
        assert shortcuts.set_telephone(12345678901) is True
        stu_info = shortcuts.get_my_info()
        assert stu_info['家庭电话'] == '12345678901'

    def test_get_unfinished_evaluation(self, shortcuts):
        shortcuts.get_unfinished_evaluation()

    def test_evaluate_course(self, shortcuts):
        # todo: 完成测试用例
        pass

    def test_get_optional_courses_and_get_course_classes(self, shortcuts):
        keys = ['学分', '开课院系', '课程代码', '课程名称', '课程类型']
        res = shortcuts.get_optional_courses()
        self.assert_every_keys(res, keys)
        keys = ['起止周', '考核类型', '教学班附加信息', '课程容量', '选中人数', '教学班号', '禁选专业', '教师', '校区', '优选范围', '开课时间,开课地点']
        for c in res:
            classes = shortcuts.get_course_classes(c['课程代码'])
            if classes:
                self.assert_every_keys(classes['可选班级'], keys)
                break

    def test_get_selected_courses(self, shortcuts):
        keys = ['费用', '教学班号', '课程名称', '课程代码', '学分', '课程类型']
        res = shortcuts.get_selected_courses()
        self.assert_every_keys(res, keys)

        assert shortcuts.check_courses(['1234567', random.choice(res)['课程代码']]) == [False, True]

    def test_change_course(self, shortcuts):
        # 参数为空
        with pytest.raises(ValueError):
            shortcuts.change_course(select_courses=None, delete_courses=None)

            # todo: 持续集成时是并行测试多个环境, 会产生不可预测的结果
            # t = session.get_system_status()
            # if t['当前轮数'] is not None:
            #     selected_courses = session.get_selected_courses()
            #     course = random.choice(selected_courses)
            #     # 选择已选中的课程
            #     rv = session.change_course(select_courses=[{'kcdm': course['课程代码'], 'jxbhs': [course['教学班号']]}])
            #     assert rv == {'删除课程': [], '选中课程': []}
            #     selectable_courses = session.get_selectable_courses(dump_result=False)
            #     if selectable_courses:
            #         course = random.choice(selectable_courses)
            #         # 选择不存在的教学班
            #         rv = session.change_course(select_courses=[{'kcdm': course['课程代码'], 'jxbhs': ['12345']}])
            #         assert rv == {'删除课程': [], '选中课程': []}
            #         jxbh = random.choice(course['可选班级'])['教学班号']
            #         # 修改班级
            #         rv = session.change_course(select_courses=[{'kcdm': course['课程代码'], 'jxbhs': [jxbh]}])
            #         # 恢复
            #         assert rv['选中课程'] == session.change_course(delete_courses=[course['课程代码']])['删除课程']
            #
            #     assert selected_courses == session.get_selected_courses()

    def test_get_selectable_courses(self, tmpdir, shortcuts):
        shortcuts.get_selectable_courses(filename=tmpdir.join('可选课程.json').strpath)
