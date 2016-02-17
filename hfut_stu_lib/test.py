# -*- coding:utf-8 -*-
from __future__ import unicode_literals, division

import logging
import unittest
import six
import os

from hfut_stu_lib import AuthSession, hfut_stu_lib_logger, STUDENT
from hfut_stu_lib.util import get_point, cal_gpa


class BaseTest(unittest.TestCase):
    hfut_stu_lib_logger.setLevel(logging.DEBUG)

    def assertEveryKeys(self, seq, keys):
        keys.sort()
        map(lambda v: self.assertListEqual(sorted(six.iterkeys(v)), keys), seq)

    def assertDictKeys(self, d, keys):
        keys.sort()
        self.assertListEqual(sorted(six.iterkeys(d)), keys)


class AuthSessionTest(BaseTest):
    def testAuthSession(self):
        self.assertRaises(ValueError, lambda: AuthSession(user_type=STUDENT))
        self.assertRaises(ValueError, lambda: AuthSession('123', '456', user_type=STUDENT))


class GuestTest(BaseTest):
    session = AuthSession()

    def test_get_class_students(self):
        keys = ['学期', '班级名称', '学生']
        res = self.session.get_class_students('025', '0400073B', '0001')
        self.assertIsNone(res)
        res = self.session.get_class_students('026', '0400073B', '0001')
        self.assertDictKeys(res, keys)
        self.assertEqual(len(res['学生']), 45)

    def test_get_class_info(self):
        keys = ['时间地点', '开课单位', '禁选范围', '考核类型', '性别限制', '教学班号', '课程名称', '优选范围', '备 注',
                '学分', '课程类型', '校区', '选中人数', '起止周']
        res = self.session.get_class_info('026', '0400073B', '0001')
        self.assertDictKeys(res, keys)

    def test_search_lessons(self):
        # todo: search_lessons 未完成, 待补充测试用例
        keys = ['班级容量', '教学班号', '课程名称', '任课教师', '课程代码', '课程类型', '序号']
        self.assertRaises(ValueError, self.session.search_lessons, '027')
        res = self.session.search_lessons('027', kcdm='1400011B')
        self.assertEveryKeys(res, keys)

    def test_get_teaching_plan(self):
        keys = ['开课单位', '学时', '课程名称', '课程代码', '学分', '序号']
        # 2013*微电子科学与工程 在 026 学期没有计划
        res = self.session.get_teaching_plan('026', '1', '0120133226')
        self.assertEqual(res, [])
        res = self.session.get_teaching_plan('027', '1', '0120133226')
        self.assertEveryKeys(res, keys)
        res = self.session.get_teaching_plan('027', '3', '0120133226')
        self.assertEveryKeys(res, keys)

    def test_get_teacher_info(self):
        keys = ['教研室', '教学课程', '学历', '教龄', '教师寄语', '简 历', '照片', '科研方向', '出生', '姓名',
                '联系电话', '职称', '电子邮件', '性别', '学位', '院系']
        res = self.session.get_teacher_info('12000198')
        self.assertDictKeys(res, keys)

    def test_get_lesson_classes(self):
        keys = ['优选范围', '教师', '教学班号']
        self.assertEveryKeys(self.session.get_lesson_classes('0521290X'), keys)
        # detail_keys = ['教师', '开课单位', '课程类型', '教学班号', '校区', '禁选范围', '时间地点', '性别限制',
        #                '课程名称', '优选范围', '备 注', '学分', '考核类型', '选中人数', '起止周']
        # self.assertEveryKeys(self.session.get_lesson_classes('0521290X', detail=True), detail_keys)


class StudentTest(BaseTest):
    session = AuthSession(2013217413, '1234567', STUDENT)

    def test_get_code(self):
        self.session.get_code()

    def test_get_stu_info(self):
        keys = ['婚姻状况', '毕业高中', '专业简称', '家庭地址', '能否选课', '政治面貌', '性别', '学院简称', '外语语种',
                '入学方式', '照片', '联系电话', '姓名', '入学时间', '籍贯', '民族', '学号', '家庭电话', '生源地',
                '出生日期', '学籍状态', '身份证号', '考生号', '班级简称', '注册状态']
        res = self.session.get_stu_info()
        self.assertDictKeys(res, keys)

    def test_get_stu_grades(self):
        keys = ['教学班号', '课程名称', '学期', '补考成绩', '课程代码', '学分', '成绩']
        res = self.session.get_stu_grades()
        self.assertEveryKeys(res, keys)

    def test_get_stu_timetable(self):
        res = self.session.get_stu_timetable()
        self.assertEqual(len(res), 7)
        map(lambda v: self.assertEqual(len(v), 11), res)

    def test_get_stu_feeds(self):
        keys = ['教学班号', '课程名称', '学期', '收费(元)', '课程代码', '学分']
        res = self.session.get_stu_feeds()
        self.assertEveryKeys(res, keys)

    def test_change_password(self):
        # 原密码不正确
        self.assertFalse(self.session.change_password('123', '123456', '123456'))
        # 新密码太短
        self.assertFalse(self.session.change_password('1234567', '12345', '12345'))
        # 新密码太长
        self.assertFalse(self.session.change_password('1234567', '1234567890123', '1234567890123'))
        # 新密码不匹配
        self.assertFalse(self.session.change_password('1234567', '12345678', '123456789'))
        # 新密码与原密码相同
        self.assertTrue(self.session.change_password('1234567', '1234567', '1234567'))
        # 新密码与原密码不同
        self.assertTrue(self.session.change_password('1234567', '123456', '123456'))
        self.assertEqual(self.session.password, '123456')
        # 改回原密码
        self.assertTrue(self.session.change_password('123456', '1234567', '1234567'))

    def test_set_telephone(self):
        self.assertFalse(self.session.set_telephone('1234567'))
        self.assertTrue(self.session.set_telephone(12345678901))
        self.assertTrue(self.session.set_telephone('12345678901'))
        stu_info = self.session.get_stu_info()
        self.assertEqual(stu_info['家庭电话'], '12345678901')

    def test_get_optional_lessons(self):
        keys = ['学分', '开课院系', '课程代码', '课程名称', '课程类型']
        res = self.session.get_optional_lessons()
        self.assertEveryKeys(res, keys)

    def test_get_selected_lessons(self):
        keys = ['费用', '教学班号', '课程名称', '课程代码', '学分', '课程类型']
        res = self.session.get_selected_lessons()
        self.assertEveryKeys(res, keys)

    def test_is_lesson_selected(self):
        self.assertFalse(self.session.is_lesson_selected('1234567'))
        self.assertFalse(self.session.is_lesson_selected('0700052B'))
        # self.assertTrue(self.session.is_lesson_selected('0532232B'))
        self.assertTrue(self.session.is_lesson_selected('1201061B'))

    def test_select_lesson(self):
        # todo: 待补充 select_lesson 测试用例
        pass

    def test_delete_lesson(self):
        # todo: 待补充 delete_lesson 测试用例
        pass


class UtilTest(BaseTest):
    session = AuthSession(2013217413, '1234567', STUDENT)

    def test_get_point(self):
        self.assertEqual(get_point('100'), 4.3)
        self.assertEqual(get_point(100), 4.3)
        self.assertEqual(get_point(90), 4.0)
        self.assertEqual(get_point(85), 3.7)
        self.assertEqual(get_point(82), 3.3)
        self.assertEqual(get_point(78), 3.0)
        self.assertEqual(get_point(75), 2.7)
        self.assertEqual(get_point(72), 2.3)
        self.assertEqual(get_point(68), 2.0)
        self.assertEqual(get_point(66), 1.7)
        self.assertEqual(get_point(64), 1.3)
        self.assertEqual(get_point(60), 1.0)
        self.assertEqual(get_point(50), 0.0)
        self.assertEqual(get_point('优'), 3.9)
        self.assertEqual(get_point('优'), 3.9)
        self.assertEqual(get_point('良'), 3.0)
        self.assertEqual(get_point('中'), 2.0)
        self.assertEqual(get_point('及格'), 1.2)
        self.assertEqual(get_point('不及格'), 0)
        self.assertRaises(AssertionError, get_point, 150)
        self.assertRaises(ValueError, get_point, '蛤蛤')

    def test_cal_gpa(self):
        self.assertIsInstance(cal_gpa(self.session.get_stu_grades()), tuple)
