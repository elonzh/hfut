# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import logging

import unittest

from lib import StuLib
from logger import logger

try:
    import uniout
except ImportError:
    logger.info('安装 uniout 库能够直接显示 unicode 内容')


class StuLibTest(unittest.TestCase):
    logger.setLevel(logging.DEBUG)
    stu = StuLib(2013217413, '1234567')
    # stu = StuLib(2013217399, '8280613')
    # stu = StuLib(2013217427, '217427')

    def assertEveryKeys(self, seq, keys):
        map(lambda v: self.assertSequenceEqual(v.keys(), keys), seq)

    def test_login(self):
        try:
            StuLib(2013217413, '123')
        except ValueError:
            pass

    def test_get_url(self):
        self.stu.get_url('login')
        self.assertRaises(KeyError, self.stu.get_url, 'test')

    def test_get_code(self):
        self.stu.get_code()

    def test_get_stu_info(self):
        keys = ['婚姻状况', '毕业高中', '专业简称', '家庭地址', '能否选课', '政治面貌', '性别', '学院简称', '外语语种',
                '入学方式', '照片', '联系电话', '姓名', '入学时间', '籍贯', '民族', '学号', '家庭电话', '生源地',
                '出生日期', '学籍状态', '身份证号', '考生号', '班级简称', '注册状态']
        res = self.stu.get_stu_info()
        self.assertEqual(res.keys(), keys)

    def test_get_stu_grades(self):
        keys = ['教学班号', '课程名称', '学期', '补考成绩', '课程代码', '学分', '成绩']
        res = self.stu.get_stu_grades()
        self.assertEveryKeys(res, keys)

    def test_get_stu_timetable(self):
        res = self.stu.get_stu_timetable()
        self.assertEqual(len(res), 7)
        map(lambda v: self.assertEqual(len(v), 11), res)
        res = self.stu.get_stu_timetable(detail=True)
        self.assertEqual(len(res), 7)

    def test_get_stu_feeds(self):
        keys = ['教学班号', '课程名称', '学期', '收费(元)', '课程代码', '学分']
        res = self.stu.get_stu_feeds()
        self.assertEveryKeys(res, keys)

    def test_get_teacher_info(self):
        keys = ['教研室', '教学课程', '学历', '教龄', '教师寄语', '简 历', '照片', '科研方向', '出生', '姓名',
                '联系电话', '职称', '电子邮件', '性别', '学位', '院系']
        res = self.stu.get_teacher_info('12000198')
        self.assertEqual(res.keys(), keys)

    def test_get_class_students(self):
        # todo: get_class_students 未完成, 待补充测试用例
        keys = ['学期', '班级名称', '学生']
        keys.sort()
        res = self.stu.get_class_students('028', '0400073B', '0001')
        self.assertIsNone(res)
        res = self.stu.get_class_students('026', '0400073B', '0001')
        res_keys = res.keys()
        res_keys.sort()
        self.assertSequenceEqual(res_keys, keys)
        self.assertEqual(len(res['学生']), 45)

    def test_get_class_info(self):
        keys = ['时间地点', '开课单位', '禁选范围', '考核类型', '性别限制', '教学班号', '课程名称', '优选范围', '备 注',
                '学分', '课程类型', '校区', '选中人数', '起止周']
        res = self.stu.get_class_info('026', '0400073B', '0001')
        self.assertEqual(res.keys(), keys)

    def test_get_lesson_detail(self):
        # todo: get_lesson_detail 未完成, 待补充测试用例
        self.assertRaises(ValueError, self.stu.get_lesson_detail, '026')
        # res = self.stu.get_lesson_detail('026', '0400073B')
        # pprint(res)

    def test_get_teaching_plan(self):
        keys = ['开课单位', '学时', '课程名称', '课程代码', '学分', '序号']
        # 2013*微电子科学与工程 在 026 学期没有计划
        res = self.stu.get_teaching_plan('026', '1', '0120133226')
        self.assertEqual(res, [])
        res = self.stu.get_teaching_plan('027', '1', '0120133226')
        self.assertEveryKeys(res, keys)
        res = self.stu.get_teaching_plan('027', '3', '0120133226')
        self.assertEveryKeys(res, keys)

    def test_change_password(self):
        # 原密码不正确
        self.assertFalse(self.stu.change_password('123', '123456', '123456'))
        # 新密码太短
        self.assertFalse(self.stu.change_password('1234567', '12345', '12345'))
        # 新密码太长
        self.assertFalse(self.stu.change_password('1234567', '1234567890123', '1234567890123'))
        # 新密码不匹配
        self.assertFalse(self.stu.change_password('1234567', '12345678', '123456789'))
        # 新密码与原密码相同
        self.assertTrue(self.stu.change_password('1234567', '1234567', '1234567'))
        # 新密码与原密码不同
        self.assertTrue(self.stu.change_password('1234567', '123456', '123456'))
        self.assertEqual(self.stu.password, '123456')
        # 改回原密码
        self.assertTrue(self.stu.change_password('123456', '1234567', '1234567'))

    def test_set_telephone(self):
        self.assertFalse(self.stu.set_telephone('1234567'))
        self.assertTrue(self.stu.set_telephone(12345678901))
        self.assertTrue(self.stu.set_telephone('12345678901'))
        stu_info = self.stu.get_stu_info()
        self.assertEqual(stu_info['家庭电话'], '12345678901')

    def test_get_optional_lessons(self):
        keys = ['学分', '开课院系', '课程代码', '课程名称', '课程类型']
        res = self.stu.get_optional_lessons()
        self.assertEveryKeys(res, keys)

    def test_get_selected_lessons(self):
        # todo: 待补充 get_selected_lessons 测试用例
        pass

    def test_is_lesson_selected(self):
        # todo: 待补充 is_lesson_selected 测试用例
        pass

    def test_get_lesson_classes(self):
        # todo: 待补充 get_lesson_classes 测试用例
        pass

    def test_select_lesson(self):
        # todo: 待补充 select_lesson 测试用例
        pass

    def test_delete_lesson(self):
        # todo: 待补充 delete_lesson 测试用例
        pass


if __name__ == '__main__':
    unittest.main()
