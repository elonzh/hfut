# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import urlparse
import re
import requests

from bs4 import SoupStrainer, BeautifulSoup

from logger import logger
from core import get_tr_strs
from util import unfinished, unstable


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


class StuLib(object):
    HOST_URL = 'http://172.18.6.99/'

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
            raise ValueError('登陆失败, 请检查你的学号和密码')
        return session

    def get_url(self, func_name):
        """
        外网 222.195.8.201
        机械工程系 172.18.6.93 172.18.6.94
        信息工程系 172.18.6.95 172.18.6.96
        化工与食品加工系 172.18.6.97
        建筑工程系 172.18.6.98
        商学系 172.18.6.99
        :param func_name:
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
            # 课程查询 POST
            'get_lesson_detail': 'student/asp/xqkb1.asp',
            # 计划查询 POST 无需登陆
            'get_teaching_plan': 'student/asp/xqkb2.asp',
            # 教师信息 GET 无需登陆
            'get_teacher_info': 'teacher/asp/teacher_info.asp',

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

        url = urlparse.urljoin(self.HOST_URL, urls[func_name])
        logger.info('获得 {} 的url:{}'.format(func_name, url))
        return url

    def get_code(self):
        """
        获取专业, 学期的代码和名称
        """
        session = self.session
        url = self.get_url('get_code')
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
        url = self.get_url('get_stu_info')
        page = session.get(url).text
        ss = SoupStrainer('table')
        bs = BeautifulSoup(page, 'html.parser', parse_only=ss)

        key_trs = bs.find_all('tr', height='16', bgcolor='#A0AAB4')
        key_lines = get_tr_strs(key_trs)
        value_trs = bs.find_all('tr', height='16', bgcolor='#D6D3CE')
        value_lines = get_tr_strs(value_trs)

        assert len(key_lines) == len(value_lines) - 2

        stu_info = {}
        # 解析前面的两行, 将第一行合并到第二行后面,因为第一行最后一列为头像
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
        url = self.get_url('get_stu_grades')
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

    @unstable
    def get_stu_timetable(self, detail=False):
        session = self.session
        url = self.get_url('get_stu_timetable')
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
        url = self.get_url('get_stu_feeds')
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
        """
        查询教师信息
        :param jsh:8位教师号
        """
        session = requests.Session()
        url = self.get_url('get_teacher_info')
        params = {'jsh': jsh}
        page = session.get(url, params=params).text
        ss = SoupStrainer('table')
        bs = BeautifulSoup(page, 'html.parser', parse_only=ss)

        value_list = get_tr_strs(bs.find_all('tr'))
        # 第一行最后有个照片项
        teacher_info = {'照片': value_list[0].pop()}
        # 第五行最后有两个空白
        value_list[4] = value_list[4][:2]
        # 第六行有两个 联系电话 键
        phone = value_list[5]
        teacher_info['联系电话'] = phone[1::2]
        value_list.remove(phone)
        # 解析其他项
        for v in value_list:
            for i in xrange(0, len(v), 2):
                teacher_info[v[i]] = v[i + 1]
        return teacher_info

    @unfinished
    def get_class_students(self, xqdm, kcdm, jxbh):
        """
        教学班查询
        :param xqdm: 学期代码
        :param kcdm: 课程代码
        :param jxbh: 教学班号
        """
        # todo: 狗日的网页代码写错了无法正确解析标签!
        session = requests.Session()
        url = self.get_url('get_class_students')
        params = {'xqdm': xqdm,
                  'kcdm': kcdm,
                  'jxbh': jxbh}
        page = session.get(url, params=params).text
        ss = SoupStrainer('table', width='500')
        bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
        if unicode(bs) == '':
            bs = BeautifulSoup(page, 'html.parser')
            msg = bs.select_one('font[color="red"] center').string.strip()
            logger.warning(','.join([msg, '请检查你的参数是否合理']))
            return None
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
        """
        url = self.get_url('get_class_info')
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
        trs = bs.find_all('tr', bgcolor='#D6D3CE')
        # 最后的 备注, 禁选范围 两行外面包裹了一个 'tr' bgcolor='#D6D3CE' 时间地点 ......
        tr4 = trs[4]
        special_kv = tuple(tr4.stripped_strings)[:2]
        trs.remove(tr4)

        value_list = get_tr_strs(trs)
        assert len(value_list) == 6

        class_info = {}
        # 前三行, 注意 value_list 第三行是有两个单元格为 None, 但key_list 用的是 tr.stripped_strings, zip 时消去了这一部分
        map(lambda seq: class_info.update(dict(zip(seq[0], seq[1]))), zip(key_list, value_list))
        # 后四行
        class_info.update(value_list[3:])
        class_info.update((special_kv,))
        return class_info

    @unfinished
    def get_lesson_detail(self, xqdm, kcdm=None, kcmc=None):
        """
        课程查询
        :param xqdm: 学期代码
        :param kcdm: 课程代码
        :param kcmc: 课程名称
        """
        # todo:完成课程查询, 使用 kcdm 无法查询成功
        if kcdm is None and kcmc is None:
            raise ValueError('kcdm 和 kcdm 参数必须至少存在一个')
        session = requests.Session()
        url = self.get_url('get_lesson_detail')
        data = {'xqdm': xqdm,
                'kcdm': kcdm,
                'kcmc': kcmc}
        page = session.post(url, data=data).text
        print page

    def get_teaching_plan(self, xqdm, kclxdm, ccjbyxzy):
        """
        计划查询
        :param xqdm: 学期代码
        :param kclxdm: 课程类型代码 必修为 1, 任选为 3
        :param ccjbyxzy: 专业
        """
        session = requests.Session()
        url = self.get_url('get_teaching_plan')

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
        """
        p = re.compile(r'^[\da-z]{6,12}$')
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
            logger.warning('密码修改失败\noldpwd: {:s}\nnewpwd: {:s}\nnew2pwd: {:s}\ntext: {:s}'.format(
                oldpwd, newpwd, new2pwd, res
            ))
            return False

    def set_telephone(self, tel):
        """
        更新电话
        :param tel: 电话号码
        """
        tel = unicode(tel)
        p = re.compile(r'^\d{11}$|^\d{4}-\d{7}$')
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
        """
        if kclx in ('x', 'b', 'jh'):
            session = self.session
            url = self.get_url('get_optional_lessons')
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
            return lessons
        else:
            raise ValueError('kclx 参数不正确!')

    def get_selected_lessons(self):
        """
        获取已选课程
        """
        session = self.session
        url = self.get_url('get_selected_lessons')
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
        获取选课系统中课程的可选教学班级
        :param kcdm:课程代码
        """
        if self.is_lesson_selected(kcdm):
            logger.warning('你已经选了课程 {:s}'.format(kcdm))
        session = requests.Session()
        params = {'kcdm': kcdm}
        url = self.get_url('get_lesson_classes')
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

    @unfinished
    def select_lesson(self, kvs):
        """
        提交选课
        :param kvs:课程代码
        :return:选课结果
        """
        # 参数中的课程代码, 用于检查参数
        kcdms = set()
        # 要提交的 kcdm 数据
        kcdms_data = []
        # 要提交的 jxbh 数据
        jxbhs_data = []
        # 函数返回的结果
        results = []
        # 参数处理
        for kv in kvs:
            kcdm = kv['kcdm']
            jxbhs = kv['jxbhs']
            if kcdm not in kcdms:
                if self.is_lesson_selected(kcdm):
                    logger.warning('课程 {:s} 你已经选过了'.format(kcdm))
                    kcdms.add(kcdm)
                    result = dict(kcdm=kcdm, jxbh=None, selected=False)
                    results.append(result)
                else:
                    if not jxbhs:
                        teaching_classes = self.get_lesson_classes(kcdm)
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
        selected_lessons = self.get_selected_lessons()
        for lesson in selected_lessons:
            kcdms_data.append(lesson['课程代码'])
            jxbhs_data.append(lesson['教学班号'])

        session = self.session
        data = {'xh': self.stu_id, 'kcdm': kcdms_data, 'jxbh': jxbhs_data}
        r = session.post(self.get_url('select_lesson'), data=data, allow_redirects=False)

        if r.status_code == 302:
            msg = '提交选课失败, 可能是身份验证过期或选课系统已关闭'
            logger.error(msg)
            raise ValueError(msg)
        else:
            page = r.text.encode('utf-8', 'ignore')
            ss = SoupStrainer('body')
            bs = BeautifulSoup(page, 'html.parser', parse_only=ss)

            fp = open('result.html', 'wb')
            fp.write(r.text)
            fp.close()

            strs = list(bs.stripped_strings)[0:-3]
            # ======================================== todo: 尚未完成!
            for str in strs:
                print str
            for i in xrange(0, len(strs), 2):
                result = {}
                if strs[i] == 'Microsoft OLE DB Provider for ODBC Drivers':
                    result['message'] = ''.join([strs[i], strs[i + 1]])
                    print result['message']
                else:
                    if strs[i] == '容量已满,请选择其他教学班!':
                        result['selected'] = False
                    elif strs[i]:
                        print strs[i]
                    s = strs[i + 1].split()
                    result['kcdm'] = s[1]
                    result['jxbh'] = s[3]
                    print result['kcdm'], result['jxbh'], result['selected']
                    results.append(result)
                    # ==================================================

    @unstable
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
            data = {'xh': self.stu_id, 'kcdm': kcdms, 'jxbh': jxbhs}
            r = session.post(self.get_url('select_lesson'), data=data,
                             allow_redirects=False)
            if r.status_code == 302:
                print '请勿同时登陆两个账号'
            else:
                new_num = len(self.get_selected_lessons())
                if new_num == old_num - 1 and not self.is_lesson_selected(kcdm):
                    print kcdm, '删除成功!'
                else:
                    print new_num, old_num
        else:
            print kcdm, '不是已选课程'
