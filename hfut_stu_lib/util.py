# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import sys

reload(sys)
sys.setdefaultencoding('utf-8')


def get_point(grade_str):
    """
    根据成绩判断绩点
    :param grade_str: 一个字符串,因为可能是百分制成绩或等级制成绩
    :return: 一个成绩绩点,为浮点数
    """
    try:
        grade = float(grade_str)
        assert 0 <= grade <= 100
        if 95 <= grade <= 100:
            return 4.3
        elif 90 <= grade < 95:
            return 4.0
        elif 85 <= grade < 90:
            return 3.7
        elif 82 <= grade < 85:
            return 3.3
        elif 78 <= grade < 82:
            return 3.0
        elif 75 <= grade < 78:
            return 2.7
        elif 72 <= grade < 75:
            return 2.3
        elif 68 <= grade < 72:
            return 2.0
        elif 66 <= grade < 68:
            return 1.7
        elif 64 <= grade < 66:
            return 1.3
        elif 60 <= grade < 64:
            return 1.0
        else:
            return 0.0
    except ValueError:
        if grade_str == '优':
            return 3.9
        elif grade_str == '良':
            return 3.0
        elif grade_str == '中':
            return 2.0
        elif grade_str == '及格':
            return 1.2
        elif grade_str == '不及格':
            return 0.0
        else:
            raise ValueError('{:s} 不是有效的成绩'.format(grade_str))


def cal_gpa(grades):
    """
    根据成绩数组计算课程平均绩点和 gpa
    :param grades: parse_grades(text) 返回的成绩数组
    :return: 包含了课程平均绩点和 gpa 的元组
    """
    # 课程总数
    lessons_sum = len(grades)
    # 课程绩点和
    points_sum = 0
    # 学分和
    credit_sum = 0
    # 课程学分 x 课程绩点之和
    gpa_points_sum = 0
    for grade in grades:
        sec_test_grade = grade.get('补考成绩')
        if sec_test_grade:
            point = get_point(sec_test_grade)
        else:
            point = get_point(grade['成绩'])
        credit = float(grade['学分'])
        points_sum += point
        credit_sum += credit
        gpa_points_sum += credit * point
    ave_point = points_sum / lessons_sum
    gpa = gpa_points_sum / credit_sum
    return ave_point, gpa
