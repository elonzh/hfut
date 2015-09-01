# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import sys

reload(sys)
sys.setdefaultencoding('utf-8')
"""
api操作对应的爬虫
"""
import json
import urlparse
import re
import time
from pprint import pprint

import requests
from bs4 import SoupStrainer, BeautifulSoup

from hfut_stu_lib import hfut_stu_lib_logger


# todo: 尚未补充异常处理，待功能完善后进行补充
JSON_CODE = {200: "查询到的正确结果",
             100: "请求格式错误或服务器处理异常, 请加群 313903239 进行反馈",
             101: "非法请求, 没有获取到json数据",
             301: "辅导员暂未开启评测或评测已结束, 请联系你的导员开启评测",
             302: "你已经提交了评测 _(:зゝ∠)_ , 不能再改了哦~",
             303: "你提交的评测人数不正确 _(:зゝ∠)_",
             304: "你不能评测你自己"}


def render_result(code=200, result=None):
    base_dict = {'code': code, 'result': JSON_CODE[code]}
    if code == 200 and result is not None:
        try:
            assert isinstance(result, (list, dict, str))
        except AssertionError:
            raise TypeError('result 类型错误！')
        base_dict['result'] = result
    hfut_stu_lib_logger.info("json rendered: {}".format(base_dict))
    return base_dict


def cal_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.clock()
        res = func(*args, **kwargs)
        hfut_stu_lib_logger.info('{:s} 执行用时: {:f}'.format(func.__name__, time.clock() - start_time))
        return res

    return wrapper


def get_point(grade_str):
    """
    根据成绩判断绩点
    :param grade_str: 一个字符串，因为可能是百分制成绩或等级制成绩
    :return: 一个成绩绩点，为浮点数
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
        assert grade_str in ('优', '良', '中', '及格', '不及格')
        if grade_str == '优':
            return 3.9
        elif grade_str == '良':
            return 3.0
        elif grade_str == '中':
            return 2.0
        elif grade_str == '及格':
            return 1.2
        else:
            return 0.0


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


def get_tr_strs(trs):
    """
    将没有值但有必须要的单元格的值设置为 None
    将 <tr> 标签数组内的单元格文字解析出来并返回一个二维列表
    :param trs: <tr> 标签数组, 为 BeautifulSoup 节点对象
    :return: 二维列表
    """
    tr_strs = []
    for tr in trs:
        strs = []
        for td in tr.find_all('td'):
            # 使用 stripped_strings 防止 td 中还有标签
            # 如: 不及格课程会有一个<font>标签导致tds[i].string为None
            # <FONT COLOR=#FF0000>37    </FONT></TD>
            # stripped_strings 是一个生成器, 没有长度
            # 生成器迭代一次就没有了, 需要转换为 tuple 或 list 进行保存
            s_list = tuple(td.stripped_strings)
            l = len(s_list)
            if l == 1:
                strs.append(s_list[0])
            elif l == 0:
                strs.append(None)
            else:
                msg = 'td标签中含有多个字符串\n{:s}'.format(td)
                print s_list
                raise ValueError(msg)
        tr_strs.append(strs)
    return tr_strs


class StuLib(object):
    HOST_URL = 'http://172.18.6.99/'
    # 可选课程缓存 todo: 全局缓存可能更有效，当然数据库缓存是最有效的，但是需要解决缓存更新的问题
    optional_lessons_cache = {'x': None, 'b': None, 'jh': None}
    selected_lessons_cache = None

    def __init__(self, stu_id, password):
        self.stu_id = stu_id
        self.password = password
        self.session = self.login()

    def login(self):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0}"}
        login_url = self.get_url('login')
        data = {"UserStyle": 'student', "user": self.stu_id, "password": self.password}
        session = requests.Session()
        session.headers = headers
        r = session.post(login_url, data=data, allow_redirects=False)
        if r.status_code != 302:
            raise ValueError('登陆失败！')
        return session

    def get_url(self, url_code):
        """
        外网 222.195.8.201
        机械工程系 172.18.6.93 172.18.6.94
        信息工程系 172.18.6.95 172.18.6.96
        化工与食品加工系 172.18.6.97
        建筑工程系 172.18.6.98
        商学系 172.18.6.99
        :param url_code:
        :return:
        """
        urls = {
            # 登陆页
            'login': 'pass.asp',
            # 需要登陆
            # 个人信息查询
            'stu_info': 'student/asp/xsxxxxx.asp',
            # 成绩查询
            'stu_grades': 'student/asp/Select_Success.asp',
            # 课表查询
            'stu_timetable': 'student/asp/grkb1.asp',
            # 收费查询
            'stu_feeds': 'student/asp/Xfsf_Count.asp',
            # 查询学期代码与专业代码
            'code': 'student/asp/xqjh.asp',
            # 修改密码 POST oldpwd=hfutxcstu&newpwd=hfutxcstu&new2pwd=hfutxcstu
            'change_password': 'student/asp/amend_password_jg.asp',
            # 修改电话 POST tel=110
            'set_telephone': 'student/asp/amend_tel.asp',

            # 无需登陆
            # 教学班查询 GET xqdm=026&kcdm=0400073B&jxbh=0001
            'class_students': 'student/asp/Jxbmdcx_1.asp',
            # 教学班详情, 选课时用得上 GET kcdm=0532082B&jxbh=0003&xqdm=026
            'class_info': 'student/asp/xqkb1_1.asp',
            # 课程查询 POST xqdm=021&kcdm=&kcmc=%D3%A2%D3%EF
            'kccx': 'student/asp/xqkb1.asp',
            # 计划查询 POST xqdm=021&kclxdm=1&ccjbyxzy=0120123111
            'jhcx': 'student/asp/xqkb2.asp',

            # ========== 选课功能相关 ==========
            # 第一轮
            # 可选课程 需要登陆 GET kclx=x
            'optional_lessons': 'student/asp/select_topLeft.asp',
            # 教学班级 无需登录
            'lesson_classes': 'student/asp/select_topRight.asp',
            # 已选中课程
            # '': 'student/asp/select_downLeft.asp',
            # 已选课程
            # '': 'student/asp/select_downRight.asp',
            # 提交选课 POST xh=2013217413&kcdm=9900037X&jxbh=0001
            # 'select_lesson': 'student/asp/selectKC_submit.asp',
            # 第三轮
            # 可选课程 需要登陆 GET kclx=x 结果与第一轮一致
            # '': 'student/asp/select_topLeft_f3.asp',
            # 教学班级 无需登录 GET 没有课程容量时间等信息
            # 'lesson_classes': 'student/asp/select_topRight_f3.asp',
            # 已选课程
            'selected_lessons': 'student/asp/select_down_f3.asp',
            # 提交选课
            'select_lesson': 'student/asp/selectKC_submit_f3.asp'
        }

        url = urlparse.urljoin(self.HOST_URL, urls[url_code])
        hfut_stu_lib_logger.info('获得 {} 的url:{}'.format(url_code, url))
        return url

    def get_code(self):
        """
        获取专业, 学期的代码和名称
        :return:
        """
        session = self.session
        url = self.get_url('code')
        page = session.get(url).text

        ss = SoupStrainer('select')
        bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
        xqdm_options = bs.find('select', attrs={'name': 'xqdm'}).find_all('option')
        xqdm = [{'key': node['value'], 'name': node.string.strip()} for node in xqdm_options]
        ccjbyxzy_options = bs.find('select', attrs={'name': 'ccjbyxzy'}).find_all('option')
        ccjbyxzy = [{'key': node['value'], 'name': node.string.strip()} for node in ccjbyxzy_options]
        result = {'xqdm': xqdm, 'ccjbyxzy': ccjbyxzy}
        return result

    def get_stu_info(self):
        session = self.session
        url = self.get_url('stu_info')
        page = session.get(url).text
        ss = SoupStrainer('table')
        bs = BeautifulSoup(page, 'html.parser', parse_only=ss)

        key_trs = bs.find_all('tr', height='16', bgcolor='#A0AAB4')
        key_lines = get_tr_strs(key_trs)
        value_trs = bs.find_all('tr', height='16', bgcolor='#D6D3CE')
        value_lines = get_tr_strs(value_trs)

        assert len(key_lines) == len(value_lines) - 2

        stu_info = {}
        # 解析前面的两行, 将第一行合并到第二行后面，因为第一行最后一列为头像
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
        url = 'student/photo/{:s}/{:d}.JPG'.format(unicode(self.stu_id)[:4], self.stu_id)
        stu_info['照片'] = urlparse.urljoin(self.HOST_URL, url)

        return stu_info

    def get_stu_grades(self):
        session = self.session
        url = self.get_url('stu_grades')
        page = session.get(url).text
        ss = SoupStrainer('table', width='582')
        bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
        trs = bs.find_all('tr')
        keys = tuple(trs[0].stripped_strings)
        # 不包括表头行和表底学分统计行
        values_list = get_tr_strs(trs[1:-1])
        grades = []
        for values in values_list:
            grade = dict(zip(keys, values))
            grades.append(grade)
        return grades

    def get_stu_timetable(self, detail=False):
        session = self.session
        url = self.get_url('stu_timetable')
        page = session.get(url).text
        ss = SoupStrainer('table', width='840')
        bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
        trs = bs.find_all('tr')
        origin_list = get_tr_strs(trs[1:])

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

    def get_stu_feeds(self):
        session = self.session
        url = self.get_url('stu_feeds')
        page = session.get(url).text
        ss = SoupStrainer('table', bgcolor='#000000')
        bs = BeautifulSoup(page, 'html.parser', parse_only=ss)

        keys = tuple(bs.table.thead.tr.stripped_strings)
        value_trs = bs.find_all('tr', bgcolor='#D6D3CE')
        value_list = [tr.stripped_strings for tr in value_trs]
        feeds = []
        for values in value_list:
            feed = dict(zip(keys, values))
            feeds.append(feed)
        return feeds

    def get_teacher_info(self, jsh):
        '''
        查询教师信息
        :param jsh:8位教师号
        :return:返回查询结果
        '''
        # todo:完成教师信息解析
        session = self.session
        r = session.get('http://222.195.8.201/teacher/asp/teacher_info.asp?jsh=%s' % jsh)
        if '无该教师信息' in r.text:
            return None
        return r

    def get_class_students(self, xqdm, kcdm, jxbh):
        """
        教学班查询
        :param xqdm: 学期代码
        :param kcdm: 课程代码
        :param jxbh: 教学班号
        :return:
        """
        session = requests.Session()
        url = self.get_url('class_students')
        params = {'xqdm': xqdm,
                  'kcdm': kcdm,
                  'jxbh': jxbh}
        page = session.get(url, params=params).text
        ss = SoupStrainer('table', width='500')
        bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
        trs = bs.find_all('tr')

        class_detail = {}
        # 学期
        term = trs[0].text.strip()
        class_detail['学期'] = term
        # 班级名称
        # 二逼教务系统将 <tr> 标签写成了 <td> , 只好直接访问兄弟节点取得这个值
        class_name = bs.table.tbody.tr.next_sibling.next_sibling.text.strip()
        class_detail['班级名称'] = class_name

        keys = tuple(trs[1].stripped_strings)
        value_list = [tr.stripped_strings for tr in trs[2:]]
        stus = []
        for values in value_list:
            stu = dict(zip(keys, values))
            stus.append(stu)
        class_detail['学生'] = stus
        return class_detail

    def get_class_info(self, xqdm, kcdm, jxbh):
        """
        获取教学班详情
        :param xqdm: 学期代码
        :param kcdm: 课程代码
        :param jxbh: 教学班号
        :return:
        """
        url = self.get_url('class_info')
        params = {'xqdm': xqdm,
                  'kcdm': kcdm,
                  'jxbh': jxbh}
        session = requests.Session()

        page = session.get(url, params=params).text
        ss = SoupStrainer('table', width='600')
        bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
        # 有三行
        key_list = [tr.stripped_strings for tr in bs.find_all('tr', bgcolor='#B4B9B9')]
        assert len(key_list) == 3
        # 有六行, 前三行与 key_list 对应, 后四行是单行属性, 键与值在同一行
        # todo: get_tr_strs 处理失败
        value_list = get_tr_strs(bs.find_all('tr', bgcolor='#D6D3CE'))
        assert len(value_list) == 7

        class_info = {}
        # 前三行, 注意 value_list 第三行是有两个单元格为 None, 但key_list 用的是 tr.stripped_strings, zip 时消去了这一部分
        map(lambda seq: class_info.update(dict(zip(seq[0], seq[1]))), zip(key_list, value_list))
        # 后四行
        class_info.update(dict(value_list[3:]))
        return class_info

    def get_lesson_detail(self, xqdm, kcdm=None, kcmc=None):
        """
        课程查询
        :param xqdm: 学期代码
        :param kcdm: 课程代码
        :param kcmc: 课程名称
        :return:
        """
        if kcdm is None and kcmc is None:
            # todo: 返回错误提示信息, 待json规范完成后进行补充
            return False
        session = requests.Session()
        # session.headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        url = self.get_url('kccx')
        data = {'xqdm': xqdm,
                'kcdm': kcdm,
                # todo: 使用 kcdm 无法查询成功
                'kcmc': kcmc}
        page = session.post(url, data=data).text
        print page

    def get_teaching_plan(self, xqdm, kclxdm, ccjbyxzy):
        """
        计划查询
        :param xqdm: 学期代码
        :param kclxdm: 课程类型代码
        :param ccjbyxzy: 专业
        :return:
        """
        session = requests.Session()
        url = self.get_url('jhcx')

        data = {'xqdm': xqdm,
                'kclxdm': kclxdm,
                'ccjbyxzy': ccjbyxzy}
        page = session.post(url, data=data).text
        ss = SoupStrainer('table', width='650')
        bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
        trs = bs.find_all('tr')
        keys = tuple(trs[1].stripped_strings)
        value_list = [tr.stripped_strings for tr in trs[2:]]
        teaching_plan = []
        for values in value_list:
            plan = dict(zip(keys, values))
            teaching_plan.append(plan)
        return teaching_plan

    def change_password(self, oldpwd, newpwd, new2pwd):
        """
        修改密码
        :param oldpwd: 旧密码
        :param newpwd: 新密码
        :param new2pwd: 重复新密码
        :return:
        """
        p = re.compile(r'[\da-zA-Z]{6,12}')
        # 若不满足密码修改条件便不做请求
        if oldpwd != self.password or newpwd != new2pwd or not p.match(newpwd):
            return False
        # 若新密码与原密码相同, 直接返回 True
        if newpwd == oldpwd:
            return True

        session = self.session
        url = self.get_url('change_password')

        data = {'oldpwd': oldpwd,
                'newpwd': newpwd,
                'new2pwd': new2pwd}
        page = session.post(url, data=data).text
        ss = SoupStrainer('table', width='580', border='0', cellspacing='1', bgcolor='#000000')
        bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
        res = bs.text.strip()
        if res == '密码修改成功！':
            self.password = newpwd
            return True
        else:
            hfut_stu_lib_logger.warning(res)
            return False

    def set_telephone(self, tel):
        """
        更新电话
        :param tel: 电话号码
        :return:
        """
        p = re.compile(r'[\d-]{7,13}')
        if not p.match(tel):
            return False

        session = self.session
        url = self.get_url('set_telephone')
        data = {'tel': tel}
        page = session.post(url, data=data).text
        ss = SoupStrainer('input', attrs={'name': 'tel'})
        bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
        return bs.input['value'] == tel

    # ========== 选课功能相关 ==========
    def get_optional_lessons(self, kclx='x'):
        """
        获取可选课程, 并不判断是否选满
        :param kclx: 课程类型参数,只有三个值,{x:全校公选课, b:全校必修课, jh:本专业计划},默认为'x'
        :return:
        """
        if self.optional_lessons_cache[kclx]:
            return self.optional_lessons_cache[kclx]['已满'].extend(self.optional_lessons_cache[kclx]['未满'])
        if kclx in ('x', 'b', 'jh'):
            session = self.session
            url = self.get_url('optional_lessons')
            params = {'kclx': kclx}
            page = session.get(url, params=params, allow_redirects=False).text
            ss = SoupStrainer('table', id='KCTable')
            bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
            lessons = []
            trs = bs.find_all('tr')
            value_list = [tuple(tr.stripped_strings) for tr in trs[:-1]]
            for values in value_list:
                lesson = {'课程代码': values[0],
                          '课程名称': values[1],
                          '课程类型': values[2],
                          '开课院系': values[3],
                          '学分': values[4]}
                lessons.append(lesson)
            self.optional_lessons_cache[kclx] = {'已满': [], '未满': lessons}
            return lessons
        else:
            raise ValueError('kclx 参数不正确！')

    def get_selected_lessons(self):
        """
        获取已选课程
        :return:已选课程信息
        """
        if self.selected_lessons_cache:
            return self.selected_lessons_cache
        session = self.session
        url = self.get_url('selected_lessons')
        page = session.get(url, allow_redirects=False).text
        ss = SoupStrainer('table', id='TableXKJG')
        bs = BeautifulSoup(page, 'html.parser', parse_only=ss)

        lessons = []
        keys = tuple(bs.find('tr', bgcolor='#296DBD').stripped_strings)
        value_list = [tr.stripped_strings for tr in bs.find_all('tr', bgcolor='#D6D3CE')]
        for values in value_list:
            lesson = dict(zip(keys, values))
            lessons.append(lesson)
        return lessons

    def is_lesson_selected(self, kcdm):
        """
        检查课程是否被选
        :param kcdm:课程代码
        :return:已选返回True,未选返回False
        """
        selected_lessons = self.get_selected_lessons()
        for lesson in selected_lessons:
            if kcdm == lesson['课程代码']:
                return True
        return False

    def get_lesson_classes(self, kcdm, detail=False):
        """
        获取教学班级
        :param kcdm:课程代码
        :return:教学班级信息
        """
        if self.is_lesson_selected(kcdm):
            # todo: 已选课程会给出警告
            return None
        else:
            session = requests.Session()
            params = {'kcdm': kcdm}
            url = self.get_url('lesson_classes')
            r = session.get(url, params=params, allow_redirects=False)
            ss = SoupStrainer('table', id='JXBTable')
            bs = BeautifulSoup(r.text, 'html.parser', parse_only=ss)
            trs = bs.find_all('tr')

            lesson_classes = []
            for tr in trs:
                klass = {}
                tds = tr.find_all('td')
                assert len(tds) == 5
                klass['教学班号'] = tds[1].string.strip()
                klass['教师'] = tds[2].text.strip()
                klass['优选范围'] = tds[3].text.strip()

                if detail:
                    href = tds[1].a['href']
                    # 匹配当前的学期代码
                    xqdm = re.search(r"(?<=,')\d{3}(?='\))", href).group()
                    klass.update(self.get_class_info(xqdm, kcdm, klass['教学班号']))

                lesson_classes.append(klass)
            return lesson_classes

    def select_lesson(self, kcdm, jxbh=None):
        '''
        提交选课
        :param kcdm:课程代码
        :param jxbh:教学班号
        :return:选课结果
        '''
        session = self.session
        # kclxmc 课程类型名称
        kcdms = []
        jxbhs = []
        # 必须添加已选课程
        selected_lessons = self.get_selected_lessons()
        if selected_lessons is not None:
            for lesson in selected_lessons:
                kcdms.append(lesson['课程代码'])
                jxbhs.append(lesson['教学班号'])
        # 添加所选课程
        if isinstance(kcdm, (list, tuple, set)):
            # 去重
            kcdm = set(kcdm)
            for id in kcdm:
                teaching_classes = self.get_lesson_classes(id)
                if teaching_classes is not None:
                    for class_ in teaching_classes:
                        kcdms.append(id)
                        jxbhs.append(class_['教学班号'])
        # 任意班级匹配
        elif isinstance(kcdm, (unicode, str)):
            # TODO:未对jxbh做类型判断
            if jxbh is None:
                teaching_classes = self.get_lesson_classes(kcdm)
                if teaching_classes is not None:
                    for class_ in teaching_classes:
                        kcdms.append(kcdm)
                        jxbhs.append(class_['教学班号'])
            else:
                kcdms.append(kcdm)
                jxbhs.append(jxbh)
        else:
            raise TypeError
        # self.session.headers = {'Referer': 'http://222.195.8.201/student/asp/select_topLeft_f3.asp'}
        data = {'xh': self.stu_id, 'kcdm': kcdms, 'jxbh': jxbhs}
        r = session.post(self.get_url('select_lesson'), data=data, allow_redirects=False)

        if r.status_code == 302:
            print '请勿同时登陆两个账号'
        else:
            ss = SoupStrainer('body')
            bs = BeautifulSoup(r.text, parse_only=ss)
            fp = open('result.html', 'wb')
            fp.write(r.text)
            fp.close()
            strs = list(bs.stripped_strings)[0:-3]
            results = []
            # for str in strs:
            #     print str
            # todo: 只输出了结果，没有反馈到缓存中
            print '=====选课结果如下====='
            print '新提交课程数：', len(strs)
            for i in xrange(0, len(strs), 2):
                result = {}
                if strs[i] == 'Microsoft OLE DB Provider for ODBC Drivers':
                    result['message'] = ''.join([strs[i], strs[i + 1]])
                    print result['message']
                else:
                    # TODO:结果处理方式有缺陷
                    result['message'] = strs[i]
                    s = strs[i + 1].split()
                    result['id'] = s[1]
                    result['class'] = s[3]
                    results.append(result)
                    print result['message'], result['id'], result['class']
            return results

    def delete_lesson(self, kcdm):
        session = self.session
        if self.is_lesson_selected(kcdm):
            kcdms = []
            jxbhs = []
            # 必须添加已选课程
            selected_lessons = self.get_selected_lessons()
            old_num = len(selected_lessons)
            if selected_lessons is not None:
                for lesson in selected_lessons:
                    if kcdm != lesson['课程代码']:
                        kcdms.append(lesson['课程代码'])
                        jxbhs.append(lesson['教学班号'])
            # 添加所选课程
            # self.session.headers = {'Referer': 'http://222.195.8.201/student/asp/select_topLeft_f3.asp'}
            data = {'xh': self.stu_id, 'kcdm': kcdms, 'jxbh': jxbhs}
            r = session.post(self.get_url('select_lesson'), data=data,
                             allow_redirects=False)
            if r.status_code == 302:
                print '请勿同时登陆两个账号'
            else:
                new_num = len(self.get_selected_lessons())
                if new_num == old_num - 1 and not self.is_lesson_selected(kcdm):
                    print kcdm, '删除成功！'
                else:
                    print new_num, old_num
        else:
            print kcdm, '不是已选课程'


if __name__ == '__main__':
    stu = StuLib(2013217413, '1234567')
    # stu = StuLib(2013217399, '8280613')
    # stu = StuLib(2013217427, '217427')
    import uniout

    # pprint(stu.get_stu_info())
    # pprint(stu.get_stu_feeds())
    # pprint(stu.get_stu_grades())
    # pprint(stu.get_stu_timetable(detail=True))
    # pprint(stu.get_class_info(kcdm='0532082B', jxbh='0001', xqdm='027'))
    # pprint(stu.change_password(stu.password, '1234567', '1234567'))
    # pprint(stu.set_telephone('1234567890'))
    # pprint(stu.get_lesson_classes('9900037X', detail=True))
    # pprint(stu.get_selected_lessons())
    # optional_lessons = stu.get_optional_lessons(kclx='x')
    # pprint(optional_lessons)
    # pprint(stu.select_lesson('1510212X'))
    # pprint(stu.delete_lesson('1510212X'))
    # with open('optional_lessons.json', 'wb') as fp:
    #     json.dump(optional_lessons, fp, ensure_ascii=False, indent=4)
    pprint(stu.get_class_info('026', '0400073B', '0001'))
    # pprint(stu.get_lesson_detail(xqdm='026', kcdm='0532082B', kcmc=None))
    # pprint(stu.get_lesson_detail(xqdm='026', kcdm=None, kcmc='电磁场与电磁波'))
    # pprint(stu.get_code())
    # pprint(stu.get_teaching_plan(xqdm='021', kclxdm='1', ccjbyxzy='0120123111'))
