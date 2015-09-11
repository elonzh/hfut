# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import urlparse
import re
import requests

from bs4 import SoupStrainer, BeautifulSoup

from logger import logger
from core import get_tr_strs
from core import unfinished, unstable

__all__ = ['StuLib']


class StuLib(object):
    HOST_URL = 'http://222.195.8.201/'
    SITE_ENCODING = 'gbk'

    def __init__(self, stu_id, password):
        self.stu_id = stu_id
        self.password = password
        self.session = self.login()

    def login(self):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0}'}
        login_url = self.get_url('login')
        data = {"UserStyle": 'student', "user": self.stu_id, "password": self.password}
        session = requests.Session()
        session.headers = headers
        res = session.post(login_url, data=data, allow_redirects=False)
        if res.status_code != 302:
            raise ValueError('\n'.join(['登陆失败, 请检查你的学号和密码', res.request.body]))
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

        url = urlparse.urljoin(self.HOST_URL, urls[func_name])
        logger.debug('获得 {} 的url:{}'.format(func_name, url))
        return url

    def catch_response(self, func_name, method='get', need_login=False, **kwargs):
        if need_login:
            session = self.session
        else:
            session = requests.Session()
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0}'}
        session.headers = headers
        url = self.get_url(func_name)
        func = getattr(session, method.lower())

        # if kwargs.get('data'):
        #     kwargs['data'] = encode_params(kwargs['data'], encoding=self.SITE_ENCODING)
        #     print kwargs['data'], type(kwargs['data'])
        if not func:
            raise ValueError(' '.join([method, '不是一个正确的请求方式']))
        res = func(url, **kwargs)
        res.encoding = self.SITE_ENCODING
        return res

    def get_code(self):
        """
        获取专业, 学期的代码和名称
        """
        res = self.catch_response(self.get_code.func_name, need_login=True)
        page = res.text

        ss = SoupStrainer('select')
        bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
        xqdm_options = bs.find('select', attrs={'name': 'xqdm'}).find_all('option')
        xqdm = [{'key': node['value'], 'name': node.string.strip()} for node in xqdm_options]
        ccjbyxzy_options = bs.find('select', attrs={'name': 'ccjbyxzy'}).find_all('option')
        ccjbyxzy = [{'key': node['value'], 'name': node.string.strip()} for node in ccjbyxzy_options]
        result = {'xqdm': xqdm, 'ccjbyxzy': ccjbyxzy}
        return result

    def get_stu_info(self):
        res = self.catch_response(self.get_stu_info.func_name, need_login=True)
        page = res.text
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
        res = self.catch_response(self.get_stu_grades.func_name, need_login=True)
        page = res.text
        ss = SoupStrainer('table', width='582')
        bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
        trs = bs.find_all('tr')
        keys = tuple(trs[0].stripped_strings)
        # 不包括表头行和表底学分统计行
        values_list = get_tr_strs(trs[1:-1])
        grades = []
        for values in values_list:
            grade = dict(zip(keys, values))
            grade['课程代码'] = grade['课程代码'].upper()
            grades.append(grade)
        return grades

    @unstable
    def get_stu_timetable(self, detail=False):
        res = self.catch_response(self.get_stu_timetable.func_name, need_login=True)
        page = res.text
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
        res = self.catch_response(self.get_stu_feeds.func_name, need_login=True)
        page = res.text
        ss = SoupStrainer('table', bgcolor='#000000')
        bs = BeautifulSoup(page, 'html.parser', parse_only=ss)

        keys = tuple(bs.table.thead.tr.stripped_strings)
        value_trs = bs.find_all('tr', bgcolor='#D6D3CE')
        value_list = [tr.stripped_strings for tr in value_trs]
        feeds = []
        for values in value_list:
            feed = dict(zip(keys, values))
            feed['课程代码'] = feed['课程代码'].upper()
            feeds.append(feed)
        return feeds

    def get_teacher_info(self, jsh):
        """
        查询教师信息
        :param jsh:8位教师号
        """
        params = {'jsh': jsh}
        res = self.catch_response(self.get_teacher_info.func_name, params=params)
        page = res.text
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

    def get_class_students(self, xqdm, kcdm, jxbh):
        """
        教学班查询
        :param xqdm: 学期代码
        :param kcdm: 课程代码
        :param jxbh: 教学班号
        """
        params = {'xqdm': xqdm,
                  'kcdm': kcdm,
                  'jxbh': jxbh}
        res = self.catch_response(self.get_class_students.func_name, params=params)
        page = res.text
        # 狗日的网页代码写错了无法正确解析标签!
        term_p = r'\d{4}-\d{4}学年第(一|二)学期'
        term = re.search(term_p, page)
        class_name_p = r'[\u4e00-\u9fa5\w-]+\d{4}班'
        class_name = re.search(class_name_p, page)
        # 虽然 \S 能解决匹配失败中文的问题, 但是最后的结果还是乱码的
        stu_p = r'>\s*?(\d{1,3})\s*?</.*?>\s*?(\d{10})\s*?</.*?>\s*?([\u4e00-\u9fa5*]+)\s*?</'
        stus = re.findall(stu_p, page, re.DOTALL)
        if term and class_name and stus:
            stus = map(lambda v: {'序号': v[0], '学号': v[1], '姓名': v[2]}, stus)
            return {'学期': term.group(), '班级名称': class_name.group(), '学生': stus}
        elif page.find('无此教学班') != -1:
            logger.warning('无此教学班, 请检查你的参数')
            return None
        else:
            msg = '\n'.join(['没有匹配到信息, 可能出现了一些问题', page])
            logger.error(msg)
            raise ValueError(msg)

    def get_class_info(self, xqdm, kcdm, jxbh):
        """
        获取教学班详情
        :param xqdm: 学期代码
        :param kcdm: 课程代码
        :param jxbh: 教学班号
        """
        params = {'xqdm': xqdm,
                  'kcdm': kcdm,
                  'jxbh': jxbh}
        res = self.catch_response(self.get_class_info.func_name, params=params)
        page = res.text
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
    def search_lessons(self, xqdm, kcdm=None, kcmc=None):
        """
        课程查询
        :param xqdm: 学期代码
        :param kcdm: 课程代码
        :param kcmc: 课程名称
        """
        # todo:完成课程查询, 使用 kcmc 无法查询成功, 可能是请求编码有问题
        if kcdm is None and kcmc is None:
            raise ValueError('kcdm 和 kcdm 参数必须至少存在一个')
        data = {'xqdm': xqdm,
                'kcdm': kcdm,
                'kcmc': kcmc}
        res = self.catch_response(self.search_lessons.func_name, method='post', data=data)

        page = res.text
        ss = SoupStrainer('table', width='650')
        bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
        term = bs.find('font', size='3', string=re.compile(r'\d{4}-\d{4}学年第(一|二)学期'))
        title = bs.find('tr', bgcolor='#FB9E04')
        trs = bs.find_all('tr', bgcolor=re.compile(r'#D6D3CE|#B4B9B9'))
        if term and title and trs:
            lessons = []
            term = term.string.strip()
            keys = tuple(title.stripped_strings)
            value_list = [tr.stripped_strings for tr in trs]
            for values in value_list:
                lesson = dict(zip(keys, values))
                lesson['课程代码'] = lesson['课程代码'].upper()
                lessons.append(lesson)
            return {'学期': term, '课程': lessons}
        else:
            logger.warning('没有找到结果\n xqdm={:s}, kcdm={:s}, kcmc={:s}'.format(xqdm, kcdm, kcmc))
            return None

    def get_teaching_plan(self, xqdm, kclxdm, ccjbyxzy):
        """
        计划查询
        :param xqdm: 学期代码
        :param kclxdm: 课程类型代码 必修为 1, 任选为 3
        :param ccjbyxzy: 专业
        """
        data = {'xqdm': xqdm,
                'kclxdm': kclxdm,
                'ccjbyxzy': ccjbyxzy}
        res = self.catch_response(self.get_teaching_plan.func_name, method='post', data=data)
        page = res.text
        ss = SoupStrainer('table', width='650')
        bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
        trs = bs.find_all('tr')
        keys = tuple(trs[1].stripped_strings)
        value_list = [tr.stripped_strings for tr in trs[2:]]
        teaching_plan = []
        for values in value_list:
            plan = dict(zip(keys, values))
            plan['课程代码'] = plan['课程代码'].upper()
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

        data = {'oldpwd': oldpwd,
                'newpwd': newpwd,
                'new2pwd': new2pwd}
        res = self.catch_response(self.change_password.func_name, method='post', need_login=True, data=data)
        page = res.text
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

        data = {'tel': tel}
        res = self.catch_response(self.set_telephone.func_name, method='post', need_login=True, data=data)
        page = res.text
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
            params = {'kclx': kclx}
            res = self.catch_response(self.get_optional_lessons.func_name, need_login=True,
                                      params=params, allow_redirects=False)
            page = res.text
            ss = SoupStrainer('table', id='KCTable')
            bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
            lessons = []
            trs = bs.find_all('tr')
            value_list = [tuple(tr.stripped_strings) for tr in trs[:-1]]
            for values in value_list:
                lesson = {'课程代码': values[0].upper(),
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
        res = self.catch_response(self.get_selected_lessons.func_name, need_login=True, allow_redirects=False)
        page = res.text
        ss = SoupStrainer('table', id='TableXKJG')
        bs = BeautifulSoup(page, 'html.parser', parse_only=ss)

        lessons = []
        keys = tuple(bs.find('tr', bgcolor='#296DBD').stripped_strings)
        value_list = [tr.stripped_strings for tr in bs.find_all('tr', bgcolor='#D6D3CE')]
        for values in value_list:
            lesson = dict(zip(keys, values))
            lesson['课程代码'] = lesson['课程代码'].upper()
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
            if kcdm.upper() == lesson['课程代码']:
                return True
        return False

    def get_lesson_classes(self, kcdm, detail=False):
        """
        获取选课系统中课程的可选教学班级
        :param kcdm:课程代码
        """
        if self.is_lesson_selected(kcdm):
            logger.warning('你已经选了课程 {:s}, 如果你要选课的话, 请勿选取此课程代码'.format(kcdm))
        params = {'kcdm': kcdm}
        res = self.catch_response(self.get_lesson_classes, params=params, allow_redirects=False)
        page = res.text
        ss = SoupStrainer('table', id='JXBTable')
        bs = BeautifulSoup(page, 'html.parser', parse_only=ss)
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

    def select_lesson(self, kvs):
        """
        提交选课
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
                if self.is_lesson_selected(kcdm):
                    logger.warning('课程 {:s} 你已经选过了'.format(kcdm))
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

        data = {'xh': self.stu_id, 'kcdm': kcdms_data, 'jxbh': jxbhs_data}
        res = self.catch_response(self.select_lesson.func_name, method='post', need_login=True,
                                  data=data, allow_redirects=False)
        if res.status_code == 302:
            msg = '提交选课失败, 可能是身份验证过期或选课系统已关闭'
            logger.error(msg)
            raise ValueError(msg)
        else:
            page = res.text
            # 当选择同意课程的多个教学班时, 若已选中某个教学班, 再选择其他班数据库会出错,
            # 其他一些不可预料的原因也会导致数据库出错
            p = re.compile(r'(成功提交选课数据|容量已满,请选择其他教学班).+?'
                           r'课程代码：\s*([\dbBxX]+)[\s;&nbsp]*教学班号：\s*(\d{4})', re.DOTALL)
            r = p.findall(page)
            if not r:
                logger.warning('正则没有匹配到结果，可能出现了一些状况\n{:s}'.format(page))
                return None
            results = []
            for g in r:
                logger.info(' '.join(g))
                msg, kcdm, jxbh = g
                if msg == '成功提交选课数据':
                    result = {'课程代码': kcdm.upper(), '教学班号': jxbh}
                    results.append(result)
            return results

    def delete_lesson(self, kcdms):
        # 对参数进行预处理
        kcdms = set(kcdms)
        kcdms = map(lambda v: v.upper(), kcdms)

        kcdms_data = []
        jxbhs_data = []
        selected_lessons = self.get_selected_lessons()
        for lesson in selected_lessons:
            if lesson['课程代码'] not in kcdms:
                kcdms_data.append(lesson['课程代码'])
                jxbhs_data.append(lesson['教学班号'])

        data = {'xh': self.stu_id, 'kcdm': kcdms_data, 'jxbh': jxbhs_data}
        res = self.catch_response(self.select_lesson.func_name, method='post', need_login=True,
                                  data=data, allow_redirects=False)
        if res.status_code == 302:
            msg = '课程删除失败, 可能是身份验证过期或选课系统已关闭'
            logger.error(msg)
            raise ValueError(msg)
        else:
            page = res.content.decode(self.SITE_ENCODING)
            # 当选择同意课程的多个教学班时, 若已选中某个教学班, 再选择其他班数据库会出错,
            # 其他一些不可预料的原因也会导致数据库出错
            p = re.compile(r'(已成功删除下列选课数据).+?课程代码：\s*([\dbBxX]+)[\s;&nbsp]*教学班号：\s*(\d{4})',
                           re.DOTALL)
            r = p.findall(page)
            if not r:
                logger.warning('正则没有匹配到结果，可能出现了一些状况\n{:s}'.format(page))
                return None
            results = []
            for g in r:
                logger.info(' '.join(g))
                msg, kcdm, jxbh = g
                result = {'课程代码': kcdm.upper(), '教学班号': jxbh}
                results.append(result)
            return results
