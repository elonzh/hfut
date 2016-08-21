# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import random

import pytest

from hfut import HF, ValidationError, XC
from . import TestBase


class TestGuest(TestBase):
    def test_get_class_students(self):
        keys = ['学期', '班级名称', '学生']
        # 电子电路课程设计A0001班
        kcdm = '0400073B'
        jxbh = '0001'
        res = self.session.get_class_students('025', kcdm, jxbh)
        assert res == {}
        res = self.session.get_class_students('026', kcdm, jxbh)
        self.assert_dict_keys(res, keys)
        if self.session.campus == HF:
            assert len(res['学生']) == 40
        else:
            assert len(res['学生']) == 45

        # 大学语文  0001班
        self.session.get_class_students('022', '5202012B', '0001')
        # 大学英语拓展（一）0001班
        self.session.get_class_students('029', '9900039X', '0001')

    def test_get_class_info(self):
        keys = ['时间地点', '开课单位', '禁选范围', '考核类型', '性别限制', '教学班号', '课程名称', '优选范围', '备注',
                '学分', '课程类型', '校区', '选中人数', '起止周']
        res = self.session.get_class_info('026', '0400073B', '0001')
        self.assert_dict_keys(res, keys)
        res = self.session.get_class_info('028', '0532142B', '0001')
        self.assert_dict_keys(res, keys)

    def test_search_course(self):
        keys = ['班级容量', '教学班号', '课程名称', '任课教师', '课程代码', '课程类型']
        with pytest.raises(ValueError):
            self.session.search_course('027')
        res = self.session.search_course('027', kcdm='1400011B')
        self.assert_every_keys(res, keys)
        res = self.session.search_course('027', kcmc='微波')
        assert len(res) == 1
        assert self.session.search_course('000', kcmc='臭傻逼') == []

    def test_get_teaching_plan(self):
        keys = ['开课单位', '学时', '课程名称', '课程代码', '学分']
        # 2013*微电子科学与工程 在 026 学期没有计划
        res = self.session.get_teaching_plan('026', 'b', '0120133226')
        assert res == []
        res = self.session.get_teaching_plan('028', 'x')
        self.assert_every_keys(res, keys)
        if self.session.campus == XC:
            assert len(res) == 33
        else:
            assert len(res) == 126

    def test_get_teacher_info(self):
        keys = ['教研室', '教学课程', '学历', '教龄', '教师寄语', '简 历', '照片', '科研方向', '出生', '姓名',
                '联系电话', '职称', '电子邮件', '性别', '学位', '院系']
        # 张燕子 在两个校区都有记录且教师号一致
        jsh = '12000199'
        res = self.session.get_teacher_info(jsh)
        self.assert_dict_keys(res, keys)

    def test_get_course_classes(self):
        keys = ['起止周', '考核类型', '教学班附加信息', '课程容量', '选中人数', '教学班号', '禁选专业', '教师', '校区', '优选范围', '开课时间,开课地点']
        if self.session.campus == HF:
            self.assert_every_keys(self.session.get_course_classes('5100016X')['可选班级'], keys)
        else:
            self.assert_every_keys(self.session.get_course_classes('9900039X')['可选班级'], keys)

    def test_get_entire_curriculum(self):
        res = self.session.get_entire_curriculum('028')
        assert len(res['课表']) == 7
        for v in res['课表']:
            assert len(v) == 11
        res = self.session.get_entire_curriculum('000')
        assert res['起始周'] == res['结束周'] == 0


class TestStudent(TestBase):
    def test_is_expired(self):
        assert self.session.is_expired is False

    def test_password(self):
        with pytest.raises(ValidationError):
            self.session.account = 123
        with pytest.raises(ValidationError):
            self.session.password = '12345'
        with pytest.raises(ValidationError):
            self.session.campus = 'FUCK'

    def test_get_code(self):
        self.session.get_code()

    def test_get_my_info(self):
        keys = ['婚姻状况', '毕业高中', '专业简称', '家庭地址', '能否选课', '政治面貌', '性别', '学院简称', '外语语种',
                '入学方式', '照片', '联系电话', '姓名', '入学时间', '籍贯', '民族', '学号', '家庭电话', '生源地',
                '出生日期', '学籍状态', '身份证号', '考生号', '班级简称', '注册状态']
        res = self.session.get_my_info()
        self.assert_dict_keys(res, keys)

    def test_get_my_achievements(self):
        keys = ['教学班号', '课程名称', '学期', '补考成绩', '课程代码', '学分', '成绩']
        res = self.session.get_my_achievements()
        self.assert_every_keys(res, keys)

    def test_get_my_curriculum(self):
        res = self.session.get_my_curriculum()
        assert len(res['课表']) == 7
        for v in res['课表']:
            assert len(v) == 11

    def test_get_my_fees(self):
        keys = ['教学班号', '课程名称', '学期', '收费(元)', '课程代码', '学分']
        res = self.session.get_my_fees()
        self.assert_every_keys(res, keys)

    def test_change_password(self):
        if self.session.campus == HF:
            with pytest.raises(TypeError):
                self.session.change_password('123456')
        else:
            password = self.session.password
            # 新密码太短
            assert self.session.change_password('12345') is False
            # 新密码太长
            assert self.session.change_password('1234567890123') is False
            # 新密码与原密码相同
            assert self.session.change_password(password) is True
            # 新密码与原密码不同
            assert self.session.change_password('123456') is True
            assert self.session.password == '123456'
            # 改回原密码
            assert self.session.change_password(password) is True

    def test_set_telephone(self):
        assert self.session.set_telephone('1234567') is False
        assert self.session.set_telephone('12345678901') is True
        assert self.session.set_telephone(12345678901) is True
        stu_info = self.session.get_my_info()
        assert stu_info['家庭电话'] == '12345678901'

    def test_get_unfinished_evaluation(self):
        self.session.get_unfinished_evaluation()

    def test_evaluate_course(self):
        # todo: 完成测试用例
        pass

    def test_get_optional_courses(self):
        keys = ['学分', '开课院系', '课程代码', '课程名称', '课程类型']
        res = self.session.get_optional_courses()
        self.assert_every_keys(res, keys)

    def test_get_selected_courses(self):
        keys = ['费用', '教学班号', '课程名称', '课程代码', '学分', '课程类型']
        res = self.session.get_selected_courses()
        self.assert_every_keys(res, keys)

        assert self.session.check_courses(['1234567', random.choice(res)['课程代码']]) == [False, True]

    def test_change_course(self):
        # todo:需要自动调整选课测试参数
        # 选课系统未开启
        t = self.session.get_system_state()
        # 参数为空
        with pytest.raises(ValueError):
            self.session.change_course(select_courses=None, delete_courses=None)
        # 删除未选课程
        with pytest.raises(ValueError):
            self.session.change_course(select_courses=None, delete_courses=['1234567B'])
        # 选择不存在的教学班
        with pytest.raises(ValueError):
            self.session.change_course(select_courses=[{'kcdm': '9900039X', 'jxbhs': ['0008']}],
                                       delete_courses=None)
        if t['当前轮数'] is not None:
            # c = self.session.get_selected_courses()
            # 选择已选中的课程
            assert self.session.change_course([{'kcdm': '9900039X'}]) == {'删除课程': None, '选中课程': None}
            # 修改班级
            assert self.session.change_course([{'kcdm': '9900039X', 'jxbhs': ['0002']}], ['9900039X']) == {
                '删除课程': [{'学分': '0',
                          '教学班号': '0001',
                          '课程代码': '9900039X',
                          '课程名称': '大学英语拓展(一）',
                          '课程类型': '任选',
                          '费用': '0'}],
                '选中课程': [{'学分': '0',
                          '教学班号': '0002',
                          '课程代码': '9900039X',
                          '课程名称': '大学英语拓展(一）',
                          '课程类型': '任选',
                          '费用': '0'}]
            }
            # 恢复
            self.session.change_course([{'kcdm': '9900039X', 'jxbhs': ['0001']}], ['9900039X'])

    def test_get_selectable_courses(self, tmpdir):
        self.session.get_selectable_courses(filename=tmpdir.join('可选课程.json').strpath)
