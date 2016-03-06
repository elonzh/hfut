# -*- coding:utf-8 -*-
"""
一些能够帮你提升效率的辅助函数
"""
from __future__ import unicode_literals, division
import re
import six
import requests
import requests.exceptions
from threading import Thread

from .log import logger

__all__ = ['get_point', 'cal_gpa', 'cal_term_code', 'term_str2code', 'get_host_speed_rank']


def get_point(grade_str):
    """
    根据成绩判断绩点

    :param grade_str: 一个字符串,因为可能是百分制成绩或等级制成绩
    :return: 成绩绩点
    :rtype: float
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

    :param grades: :meth:`models.StudentSession.get_my_achievements` 返回的成绩数组
    :return: 包含了课程平均绩点和 gpa 的元组
    """
    # 课程总数
    courses_sum = len(grades)
    # 课程绩点和
    points_sum = 0
    # 学分和
    credit_sum = 0
    # 课程学分 x 课程绩点之和
    gpa_points_sum = 0
    for grade in grades:
        point = get_point(grade.get('补考成绩') or grade['成绩'])
        credit = float(grade['学分'])

        points_sum += point
        credit_sum += credit
        gpa_points_sum += credit * point
    ave_point = points_sum / courses_sum
    gpa = gpa_points_sum / credit_sum
    return round(ave_point, 5), round(gpa, 5)


def cal_term_code(year, is_first_term=True):
    """
    计算对应的学期代码

    :param year: 学年开始年份,例如 "2012-2013学年第二学期" 就是 2012
    :param is_first_term: 是否为第一学期
    :type is_first_term: bool
    :return: 形如 "022" 的学期代码
    """
    if year <= 2001:
        msg = '出现了超出范围年份: {}'.format(year)
        logger.critical(msg)
        raise ValueError(msg)
    term_code = (year - 2001) * 2
    if is_first_term:
        term_code -= 1
    return '%03d' % term_code


def term_str2code(term_str):
    """
    将学期字符串转换为对应的学期代码串

    :param term_str: 形如 "2012-2013学年第二学期" 的学期字符串
    :return: 形如 "022" 的学期代码
    """
    term_pattern = re.compile(r'(\d{4})-\d{4}学年\s*第(一|二)学期')
    result = term_pattern.match(term_str).groups()
    year = int(result[0])
    return cal_term_code(year, result[1] == '一')


def get_host_speed_rank(exclude=None, timeout=(5, 10)):
    """
    在宣城校区内网下测试各个内网地址的速度并返回排名

    :param exclude: 不进行计算的 IP 地址列表, 可以是 `http://222.195.8.201` 或者 `222.195.8.201` 的形式
    :param timeout: 超时时间, 可以是一个浮点数或 形如 ``(连接超时, 读取超时)`` 的元祖
    :return: 形如 ``[(地址, 速度)]`` 的排名数据
    """
    exclude = exclude or []
    hosts = [
        '222.195.8.201',
        '172.18.6.93',
        '172.18.6.94',
        '172.18.6.95',
        '172.18.6.96',
        '172.18.6.97',
        '172.18.6.98',
        '172.18.6.99'
    ]

    for addr in exclude:
        p = six.moves.urllib.parse.urlparse(addr)
        h = p.netloc or p.path
        hosts.remove(h)
        logger.debug('[%s] 被排除', h)

    available_hosts = []

    class HostCheckerThread(Thread):
        def __init__(self, host):
            super(HostCheckerThread, self).__init__()
            self.host = six.moves.urllib.parse.SplitResult('http', host, '', '', '').geturl()

        def run(self):
            try:
                res = requests.head(self.host, timeout=timeout)
            except requests.exceptions.ConnectionError:
                # 连接失败
                logger.error('[%s] 连接超时!', self.host)
            except requests.exceptions.ReadTimeout:
                # 连接超时
                logger.error('[%s] 读取超时!', self.host)
            except requests.HTTPError:
                # 服务器出错
                logger.error('[%s] 连接失败!', self.host)
            else:
                cost = res.elapsed.total_seconds() * 1000
                available_hosts.append((cost, self.host))
                logger.info('[%s] 请求成功,耗时 %.0f ms', self.host, cost)

    threads = [HostCheckerThread(u) for u in hosts]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    available_hosts.sort()
    return available_hosts
