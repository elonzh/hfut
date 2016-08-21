# -*- coding:utf-8 -*-
"""
hfut 核心的模块, 包括了 :class:`models.APIResult` 和包含各个接口的各个 ``Session`` 类, 继承关系如下:

:class:`requests.sessions.Session` ->

:class:`model.BaseSession` ->

:class:`model.GuestSession` ->

:class:`model.StudentSession`

"""
from __future__ import unicode_literals, division

import json
import re
import time
from collections import deque
from threading import Thread

import requests
import six
from bs4 import SoupStrainer, BeautifulSoup

from .exception import SystemLoginFailed, IPBanned, ValidationError
from .log import logger, log_result_not_found
from .parser import parse_tr_strs, flatten_list, dict_list_2_tuple_set, parse_course, safe_zip
from .value import XC, HF, HOSTS, TERM_PATTERN, XC_PASSWORD_PATTERN, ACCOUNT_PATTERN, HF_PASSWORD_PATTERN, \
    validate_attrs

__all__ = ['BaseSession', 'GuestSession', 'StudentSession']


def _get_curriculum(session, url, params=None):
    """
    通用的获取课表函数

    @structure {'课表': [[[{'上课周数': [int], '课程名称': str, '课程地点': str}]]], '起始周': int, '结束周': int}
    """
    method = 'get'
    response = session.api_request(method, url, params=params)

    page = response.text
    ss = SoupStrainer('table', width='840')
    bs = BeautifulSoup(page, session.html_parser, parse_only=ss)
    trs = bs.find_all('tr')
    origin_list = parse_tr_strs(trs[1:])

    # 顺时针反转矩阵
    length = len(origin_list)
    width = len(origin_list[0])
    new_matrix = []
    weeks = set()
    for i in range(width):
        newline = []
        for j in range(length):
            if origin_list[j][i] is None:
                newline.append(None)
            else:
                courses = parse_course(origin_list[j][i])
                for c in courses:
                    weeks.update(c['上课周数'])
                newline.append(courses)
        new_matrix.append(newline)
    # 去除第一行的序号
    curriculum = new_matrix[1:]
    weeks = weeks or {0}
    return {'课表': curriculum, '起始周': min(weeks), '结束周': max(weeks)}


@validate_attrs({'campus': 'validate_campus'})
class BaseSession(requests.Session):
    """
    所有接口会话类的基类
    """
    host = None
    site_encoding = 'gbk'
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/45.0.2454.101 Safari/537.36'
    }
    html_parser = 'html.parser'
    histories = deque(maxlen=10)

    def api_request(self, method, url, **kwargs):
        """
        所有接口用来发送请求的方法, 只是 :meth:`requests.sessions.Session.request` 的一个钩子方法, 用来处理请求前后的工作

        :param method: 请求方法
        :param url: 教务系统页面的相对地址
        """
        if not six.moves.urllib.parse.urlparse(url).netloc:
            url = six.moves.urllib.parse.urljoin(self.host, url)
        response = self.request(method, url, **kwargs)
        response.encoding = self.site_encoding
        self.histories.append(response)
        elapsed = response.elapsed.total_seconds() * 1000
        logger.debug('[%s] %s 请求成功,请求耗时 %d ms\n参数: %s', method, url, elapsed, kwargs)
        return response

    def __init__(self, campus):
        """
        所以接口会话类的基类

        :param campus: 校区代码, 请使用 ``value`` 模块中的 ``HF``, ``XC`` 分别来区分合肥校区和宣城校区
        """
        super(BaseSession, self).__init__()
        self.headers = self.default_headers

        # 初始化时根据合肥选择不同的地址
        self.campus = campus.upper()
        self.host = HOSTS[self.campus]

    def validate_campus(self, value):
        if value not in (XC, HF):
            raise ValidationError('校区代码只能为"XC"或者"HF"')


class GuestSession(BaseSession):
    """
    无需登录就可使用的接口
    """

    def get_system_state(self):
        """
        获取教务系统当前状态信息, 包括当前学期以及选课计划

        @structure {'当前学期': str, '选课计划': [(float, float)], '当前轮数': int or None}
        """
        method = 'get'
        url = 'student/asp/s_welcome.asp'
        response = self.api_request(method, url)
        # 学期后有一个 </br> 便签, html.parser 会私自的将它替换为 </table> 导致无获取后面的 html
        # ss = SoupStrainer('table', height='85%')
        bs = BeautifulSoup(response.text, self.html_parser)
        text = bs.get_text(strip=True)
        term = TERM_PATTERN.search(text).group()
        plan_pattern = re.compile(
            r'第(\d)轮:'
            r'(\d{4}-\d{1,2}-\d{1,2}\s+\d{1,2}:\d{1,2}:\d{1,2})'
            r'\s*到\s*'
            r'(\d{4}-\d{1,2}-\d{1,2}\s+\d{1,2}:\d{1,2}:\d{1,2})'
        )
        raw_plans = plan_pattern.findall(text)
        time_fmt = '%Y-%m-%d %X'

        plans = []
        current_round = None
        for p in raw_plans:
            # 为了支持转换到 json 使用了浮点时间
            start = time.mktime(time.strptime(p[1], time_fmt))
            end = time.mktime(time.strptime(p[2], time_fmt))
            # 每次都计算当前时间保证准确性
            now = time.time()
            if start < now < end:
                current_round = int(p[0])
            # plans.append(dict(zip(('轮数', '开始', '结束'), (int(p[0]), start, end))))
            # 结果是有顺序的
            plans.append((start, end))
        assert plans
        result = {
            '当前学期': term,
            '选课计划': plans,
            '当前轮数': current_round
        }
        return result

    def get_class_students(self, xqdm, kcdm, jxbh):
        """
        教学班查询, 查询指定教学班的所有学生

        @structure {'学期': str, '班级名称': str, '学生': [{'姓名': str, '学号': int}]}

        :param xqdm: 学期代码
        :param kcdm: 课程代码
        :param jxbh: 教学班号
        """
        method = 'get'
        url = 'student/asp/Jxbmdcx_1.asp'
        params = {'xqdm': xqdm,
                  'kcdm': kcdm.upper(),
                  'jxbh': jxbh}
        response = self.api_request(method, url, params=params)

        page = response.text
        # 狗日的网页代码写错了无法正确解析标签!
        term = TERM_PATTERN.search(page)
        # 大学英语拓展（一）0001班
        # 大学语文    0001班
        class_name_p = r'\S+\s*\d{4}班'
        class_name = re.search(class_name_p, page)
        # 虽然 \S 能解决匹配失败中文的问题, 但是最后的结果还是乱码的
        stu_p = r'>\s*?(\d{1,3})\s*?</.*?>\s*?(\d{10})\s*?</.*?>\s*?([\u4e00-\u9fa5*]+)\s*?</'
        stus = re.findall(stu_p, page, re.DOTALL)
        if term and class_name:
            # stus = [{'序号': int(v[0]), '学号': int(v[1]), '姓名': v[2]} for v in stus]
            stus = [{'学号': int(v[1]), '姓名': v[2]} for v in stus]
            return {'学期': term.group(), '班级名称': class_name.group(), '学生': stus}
        elif page.find('无此教学班') != -1:
            log_result_not_found(page)
            return {}
        else:
            msg = '\n'.join(['没有匹配到信息, 可能出现了一些问题', page])
            logger.error(msg)
            raise ValueError(msg)

    def get_class_info(self, xqdm, kcdm, jxbh):
        """
        获取教学班详情, 包括上课时间地点, 考查方式, 老师, 选中人数, 课程容量等等信息

        @structure {'校区': str,'开课单位': str,'考核类型': str,'课程类型': str,'课程名称': str,'教学班号': str,'起止周': str,
        '时间地点': str,'学分': float,'性别限制': str,'优选范围': str,'禁选范围': str,'选中人数': int,'备注': str}

        :param xqdm: 学期代码
        :param kcdm: 课程代码
        :param jxbh: 教学班号
        """
        method = 'get'
        url = 'student/asp/xqkb1_1.asp'
        params = {'xqdm': xqdm,
                  'kcdm': kcdm.upper(),
                  'jxbh': jxbh}
        response = self.api_request(method, url, params=params)

        page = response.text
        ss = SoupStrainer('table', width='600')
        bs = BeautifulSoup(page, self.html_parser, parse_only=ss)
        # 有三行 , 教学班号	课程名称	课程类型	学分  开课单位	校区	起止周	考核类型  性别限制	选中人数
        key_list = [list(tr.stripped_strings) for tr in bs.find_all('tr', bgcolor='#B4B9B9')]
        if len(key_list) != 3:
            log_result_not_found(page)
            return {}
        # 有7行, 前三行与 key_list 对应, 后四行是单行属性, 键与值在同一行
        trs = bs.find_all('tr', bgcolor='#D6D3CE')
        # 最后的 备注, 禁选范围 两行外面包裹了一个 'tr' bgcolor='#D6D3CE' 时间地点 ......
        # 如果使用 lxml 作为解析器, 会自动纠正错误
        # 前三行, 注意 value_list 第三行是有两个单元格为 None,
        value_list = parse_tr_strs(trs[:3])
        # Python3 的 map 返回的是生成器, 不会立即产生结果
        # map(lambda seq: class_info.update(dict(zip(seq[0], seq[1]))), zip(key_list, value_list))
        keys = flatten_list(key_list)
        values = flatten_list(value_list)
        class_info = dict(safe_zip(keys, values, 10, 12))
        class_info['学分'] = float(class_info['学分'])
        class_info['选中人数'] = int(class_info['选中人数'])
        # 后四行
        last_4_lines = [list(tr.stripped_strings) for tr in trs[3:7]]
        last_4_lines[1] = last_4_lines[1][:-(len(last_4_lines[2]) + len(last_4_lines[3]))]
        for kv in last_4_lines:
            k = kv[0]
            v = None if len(kv) == 1 else kv[1]
            class_info[k] = v
        class_info['备注'] = class_info.pop('备 注')
        return class_info

    def search_course(self, xqdm, kcdm=None, kcmc=None):
        """
        课程查询

        @structure [{'任课教师': str, '课程名称': str, '教学班号': str, '课程代码': str, '班级容量': int}]

        :param xqdm: 学期代码
        :param kcdm: 课程代码
        :param kcmc: 课程名称
        """
        if kcdm is None and kcmc is None:
            raise ValueError('kcdm 和 kcdm 参数必须至少存在一个')
        method = 'post'
        url = 'student/asp/xqkb1.asp'
        data = {'xqdm': xqdm,
                'kcdm': kcdm.upper() if kcdm else None,
                'kcmc': kcmc.encode(self.site_encoding) if kcmc else None}
        response = self.api_request(method, url, data=data)

        page = response.text
        ss = SoupStrainer('table', width='650')
        bs = BeautifulSoup(page, self.html_parser, parse_only=ss)
        title = bs.find('tr', bgcolor='#FB9E04')
        trs = bs.find_all('tr', bgcolor=re.compile(r'#D6D3CE|#B4B9B9'))

        if title and trs:
            courses = []
            keys = tuple(title.stripped_strings)
            value_list = parse_tr_strs(trs)
            for values in value_list:
                course = dict(safe_zip(keys, values))
                course.pop('序号')
                course['课程代码'] = course['课程代码'].upper()
                course['班级容量'] = int(course['班级容量'])
                courses.append(course)
            return courses
        else:
            log_result_not_found(page)
            return []

    def get_teaching_plan(self, xqdm, kclx='b', zydm=''):
        """
        专业教学计划查询, 可以查询全校公选课, 此时可以不填 `zydm`

        @structure [{'开课单位': str, '学时': int, '课程名称': str, '课程代码': str, '学分': float}]

        :param xqdm: 学期代码
        :param kclx: 课程类型参数,只有两个值 b:专业必修课, x:全校公选课
        :param zydm: 专业代码, 可以从 :meth:`models.StudentSession.get_code` 获得
        """
        if kclx == 'b' and not zydm:
            raise ValueError('查询专业必修课必须提供专业代码')
        kclxdm = {'b': 1, 'x': 3}[kclx]

        method = 'post'
        url = 'student/asp/xqkb2.asp'
        data = {'xqdm': xqdm,
                'kclxdm': kclxdm,
                'ccjbyxzy': zydm}
        response = self.api_request(method, url, data=data)

        page = response.text
        ss = SoupStrainer('table', width='650')
        bs = BeautifulSoup(page, self.html_parser, parse_only=ss)
        trs = bs.find_all('tr')
        keys = tuple(trs[1].stripped_strings)
        if len(keys) != 6:
            log_result_not_found(page)
            return []

        value_list = parse_tr_strs(trs[2:])
        teaching_plan = []
        for values in value_list:
            code = values[1].upper()
            if teaching_plan and teaching_plan[-1]['课程代码'] == code:
                # 宣城校区查询公选课会有大量的重复
                continue
            plan = dict(safe_zip(keys, values))
            plan.pop('序号')
            plan['课程代码'] = code
            plan['学时'] = int(plan['学时'])
            plan['学分'] = float(plan['学分'])
            teaching_plan.append(plan)
        return teaching_plan

    def get_teacher_info(self, jsh):
        """
        教师信息查询

        @structure {'教研室': str, '教学课程': str, '学历': str, '教龄': str, '教师寄语': str, '简 历': str, '照片': str,
         '科研方向': str, '出生': str, '姓名': str, '联系电话': [str], '职称': str, '电子邮件': str, '性别': str, '学位': str,
          '院系': str]

        :param jsh: 8位教师号, 例如 '05000162'
        """
        params = {'jsh': jsh}
        method = 'get'
        url = 'teacher/asp/teacher_info.asp'
        response = self.api_request(method, url, params=params)

        page = response.text
        ss = SoupStrainer('table')
        bs = BeautifulSoup(page, self.html_parser, parse_only=ss)
        if not bs.text:
            log_result_not_found(page)
            return {}
        value_list = parse_tr_strs(bs.find_all('tr'))
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
            for i in range(0, len(v), 2):
                teacher_info[v[i]] = v[i + 1]
        return teacher_info

    def get_course_classes(self, kcdm):
        """
        获取选课系统中课程的可选教学班级

        @structure {'可选班级': [{'起止周': str, '考核类型': str, '教学班附加信息': str, '课程容量': int, '选中人数': int,
         '教学班号': str, '禁选专业': str, '教师': [str], '校区': str, '优选范围': [str], '开课时间,开课地点': [str]}],
        '课程代码': str, '课程名称': str}

        :param kcdm: 课程代码
        """
        params = {'kcdm': kcdm.upper()}
        method = 'get'
        # url = 'student/asp/select_topRight.asp'
        url = 'student/asp/select_topRight_f3.asp'
        response = self.api_request(method, url, params=params)

        page = response.text
        ss = SoupStrainer('body')
        bs = BeautifulSoup(page, self.html_parser, parse_only=ss)
        class_table = bs.select_one('#JXBTable')
        if class_table.get_text(strip=True) == '对不起！该课程没有可被选的教学班。':
            return {}

        result = dict()
        _, result['课程代码'], result['课程名称'] = bs.select_one('#KcdmTable').stripped_strings
        result['课程代码'] = result['课程代码'].upper()
        trs = class_table.find_all('tr')

        course_classes = []
        for tr in trs:
            tds = tr.find_all('td')
            assert len(tds) == 5

            # 解析隐含在 alt 属性中的信息
            class_info_table = BeautifulSoup(tds[1]['alt'], self.html_parser)
            info_trs = class_info_table.select('tr')
            # 校区 起止周 考核类型 禁选专业
            cls_info = dict(safe_zip(info_trs[0].stripped_strings, parse_tr_strs([info_trs[1]])[0]))
            # 选中人数 课程容量
            for s in info_trs[2].stripped_strings:
                kv = [v.strip() for v in s.split(':', 1)]
                cls_info[kv[0]] = int(kv[1]) if kv[1] else None
            # 教学班附加信息
            # 教学班附加信息：屯溪路校区 上课地点：体育部办公楼2楼
            for s in info_trs[5].stripped_strings:
                kv = s.split('：', 1)
                cls_info[kv[0].strip()] = kv[1].strip() or None
            # 开课时间,开课地点
            p = re.compile(r'周[一二三四五六日]:\(\d+-\d+节\) \(\d+-\d+周\).+?\d+')
            cls_info[info_trs[3].get_text(strip=True)] = p.findall(info_trs[4].get_text(strip=True))

            cls_info['课程容量'] = int(cls_info['课程容量'])
            cls_info['选中人数'] = int(cls_info['选中人数'])
            cls_info['教学班号'] = tds[1].string.strip()
            cls_info['教师'] = [s.strip() for s in tds[2].text.split(',')]
            cls_info['优选范围'] = [s.strip() for s in tds[3].text.split(',')]

            course_classes.append(cls_info)

        result['可选班级'] = course_classes
        return result

    def get_entire_curriculum(self, xqdm=None):
        """
        获取全校的学期课程表, 当没有提供学期代码时默认返回本学期课程表

        @structure {'课表': [[[{'上课周数': [int], '课程名称': str, '课程地点': str}]]], '起始周': int, '结束周': int}

        :param xqdm: 学期代码
        """
        url = 'teacher/asp/Jskb_table.asp'
        params = {'xqdm': xqdm}
        return _get_curriculum(self, url, params=params)


@validate_attrs({'account': 'validate_account', 'password': 'validate_password'})
@six.python_2_unicode_compatible
class StudentSession(GuestSession):
    """
    学生教务接口, 继承了 :class:`models.GuestSession` 的所有接口, 因此一般推荐使用这个类
    """

    def __init__(self, account, password, campus):
        """
        :param account: 学号
        :param password: 密码
        """
        # 先初始化状态才能登陆
        super(StudentSession, self).__init__(campus)

        self.account = account
        self.password = password
        self.name = None
        self.last_request_at = 0

    def __str__(self):
        return '<StudentSession:{account}>'.format(account=self.account)

    def validate_account(self, value):
        value = six.text_type(value)
        if not ACCOUNT_PATTERN.match(value):
            raise ValidationError('学号为10位数字')

    def validate_password(self, value):
        if self.campus == HF:
            if not HF_PASSWORD_PATTERN.match(value):
                raise ValidationError('合肥校区信息中心密码为6-16位')
        elif self.campus == XC:
            if not XC_PASSWORD_PATTERN.match(value):
                raise ValidationError('宣城校区教务密码为6-12位小写字母或数字')

    @property
    def is_expired(self):
        """
        asp.net 如果程序中没有设置session的过期时间,那么session过期时间就会按照IIS设置的过期时间来执行,
        IIS中session默认过期时间为20分钟,网站配置 最长24小时,最小15分钟, 页面级>应用程序级>网站级>服务器级.
        .那么当超过 15 分钟未操作会认为会话已过期需要重新登录

        :return: 会话是否过期
        """
        now = time.time()
        return (now - self.last_request_at) >= 15 * 60

    def login(self):
        """
        登录账户
        """
        # 登陆前清空 cookie, 能够防止再次登陆时因携带 cookie 可能提示有未进行教学评估的课程导致接口不可用
        self.cookies.clear_session_cookies()

        if self.campus == HF:
            login_data = {'IDToken1': self.account, 'IDToken2': self.password}
            login_url = 'http://ids1.hfut.edu.cn/amserver/UI/Login'
            super(StudentSession, self).api_request('post', login_url, data=login_data)

            method = 'get'
            url = 'StuIndex.asp'
            data = None
        else:
            method = 'post'
            url = 'pass.asp'
            data = {"user": self.account, "password": self.password, "UserStyle": 'student'}
        # 使用重载的 api_request 会造成递归调用
        response = super(StudentSession, self).api_request(method, url, data=data, allow_redirects=False)
        logged_in = response.status_code == 302
        if not logged_in:
            if 'SQL通用防注入系统' in response.text:
                msg = '当前 IP 已被锁定,如果是宣城校内访问请切换教务系统地址,否则请在更换网络环境后重试'
                logger.warning(msg)
                raise IPBanned(msg)
            else:
                msg = '登陆失败, 请检查你的账号和密码'
                logger.error(msg)
                raise SystemLoginFailed(msg)

        escaped_name = self.cookies.get('xsxm')
        # https://pythonhosted.org/six/#module-six.moves.urllib.parse
        if six.PY3:
            self.name = six.moves.urllib.parse.unquote(escaped_name, self.site_encoding)
        else:
            name = six.moves.urllib.parse.unquote(escaped_name)
            self.name = name.decode(self.site_encoding)

    def api_request(self, method, url, **kwargs):

        if self.is_expired:
            self.login()
        self.last_request_at = time.time()

        return super(StudentSession, self).api_request(method, url, **kwargs)

    def get_code(self):
        """
        获取当前所有的学期, 学期以及对应的学期代码, 注意如果你只是需要获取某个学期的代码的话请使用 :func:`util.cal_term_code`

        @structure {'专业': [{'专业代码': str, '专业名称': str}], '学期': [{'学期代码': str, '学期名称': str}]}

        """
        method = 'get'
        url = 'student/asp/xqjh.asp'
        response = self.api_request(method, url)
        page = response.text

        ss = SoupStrainer('select')
        bs = BeautifulSoup(page, self.html_parser, parse_only=ss)
        xqdm_options = bs.find('select', attrs={'name': 'xqdm'}).find_all('option')
        xqdm = [{'学期代码': node['value'], '学期名称': node.string.strip()} for node in xqdm_options]
        ccjbyxzy_options = bs.find('select', attrs={'name': 'ccjbyxzy'}).find_all('option')
        ccjbyxzy = [{'专业代码': node['value'], '专业名称': node.string.strip()} for node in ccjbyxzy_options]
        result = {'学期': xqdm, '专业': ccjbyxzy}

        return result

    def get_my_info(self):
        """
        获取个人信息

        @structure {'婚姻状况': str, '毕业高中': str, '专业简称': str, '家庭地址': str, '能否选课': str, '政治面貌': str,
         '性别': str, '学院简称': str, '外语语种': str, '入学方式': str, '照片': str, '联系电话': str, '姓名': str,
         '入学时间': str, '籍贯': str, '民族': str, '学号': int, '家庭电话': str, '生源地': str, '出生日期': str,
         '学籍状态': str, '身份证号': str, '考生号': int, '班级简称': str, '注册状态': str}
        """
        method = 'get'
        url = 'student/asp/xsxxxxx.asp'
        response = self.api_request(method, url)

        page = response.text
        ss = SoupStrainer('table')
        bs = BeautifulSoup(page, self.html_parser, parse_only=ss)

        key_trs = bs.find_all('tr', height='16', bgcolor='#A0AAB4')
        key_lines = parse_tr_strs(key_trs)
        value_trs = bs.find_all('tr', height='16', bgcolor='#D6D3CE')
        # img 标签没有文字, 照片项为 None
        value_lines = parse_tr_strs(value_trs)

        assert len(key_lines) == len(value_lines) - 2

        stu_info = {}
        # 解析前面的两行, 将第一行合并到第二行后面,因为第一行最后一列为头像
        value_lines[1].extend(value_lines[0])
        kvs = []
        for cell in value_lines[1][:-1]:
            kv_tuple = (v.strip() for v in cell.split(':', 1))
            kvs.append(kv_tuple)
        stu_info.update(kvs)

        # 解析后面对应的信息
        for line in safe_zip(key_lines, value_lines[2:]):
            stu_info.update(safe_zip(line[0], line[1]))

        # 添加照片项
        photo_url = six.moves.urllib.parse.urljoin(response.url, bs.select_one('td[rowspan=6] img')['src'])
        stu_info['照片'] = photo_url

        stu_info['学号'] = int(stu_info['学号'])
        stu_info['考生号'] = int(stu_info['考生号'])
        return stu_info

    def get_my_achievements(self):
        """
        获取个人成绩

        @structure [{'教学班号': str, '课程名称': str, '学期': str, '补考成绩': str, '课程代码': str, '学分': float, '成绩': str}]
        """
        method = 'get'
        url = 'student/asp/Select_Success.asp'
        response = self.api_request(method, url)

        page = response.text
        ss = SoupStrainer('table', width='582')
        bs = BeautifulSoup(page, self.html_parser, parse_only=ss)
        trs = bs.find_all('tr')
        keys = tuple(trs[0].stripped_strings)
        # 不包括表头行和表底学分统计行
        values_list = parse_tr_strs(trs[1:-1])
        grades = []
        for values in values_list:
            grade = dict(safe_zip(keys, values))
            grade['课程代码'] = grade['课程代码'].upper()
            grade['学分'] = float(grade['学分'])
            grades.append(grade)
        return grades

    def get_my_curriculum(self):
        """
        获取个人课表

        @structure {'课表': [[[{'上课周数': [int], '课程名称': str, '课程地点': str}]]], '起始周': int, '结束周': int}
        """
        url = 'student/asp/grkb1.asp'
        return _get_curriculum(self, url)

    def get_my_fees(self):
        """
        收费查询

        @structure [{'教学班号': str, '课程名称': str, '学期': str, '收费(元): float', '课程代码': str, '学分': float}]
        """
        method = 'get'
        url = 'student/asp/Xfsf_Count.asp'
        response = self.api_request(method, url)

        page = response.text
        ss = SoupStrainer('table', bgcolor='#000000')
        bs = BeautifulSoup(page, self.html_parser, parse_only=ss)

        keys = tuple(bs.table.thead.tr.stripped_strings)
        value_trs = bs.find_all('tr', bgcolor='#D6D3CE')
        value_list = parse_tr_strs(value_trs)
        feeds = []
        for values in value_list:
            feed = dict(safe_zip(keys, values))
            feed['课程代码'] = feed['课程代码'].upper()
            feed['学分'] = float(feed['学分'])
            feed['收费(元)'] = float(feed['收费(元)'])
            feeds.append(feed)
        return feeds

    def change_password(self, new_password):
        """
        修改教务密码, **注意**合肥校区使用信息中心账号登录, 与教务密码不一致, 即使修改了也没有作用, 因此合肥校区帐号调用此接口会直接报错

        @structure bool

        :param new_password: 新密码
        """
        if self.campus == HF:
            raise TypeError('合肥校区使用信息中心账号登录, 修改教务密码没有作用')
        # 若新密码与原密码相同, 直接返回 True
        if new_password == self.password:
            msg = '原密码与新密码相同'
            logger.warning(msg)
            return True
        # 若不满足密码修改条件便不做请求
        if not XC_PASSWORD_PATTERN.match(new_password):
            msg = '密码为6-12位小写字母或数字'
            logger.warning(msg)
            return False

        method = 'post'
        url = 'student/asp/amend_password_jg.asp'
        data = {'oldpwd': self.password,
                'newpwd': new_password,
                'new2pwd': new_password}
        response = self.api_request(method, url, data=data)

        page = response.text
        ss = SoupStrainer('table', width='580', border='0', cellspacing='1', bgcolor='#000000')
        bs = BeautifulSoup(page, self.html_parser, parse_only=ss)
        res = bs.text.strip()
        if res == '密码修改成功！':
            self.password = new_password
            return True
        else:
            logger.warning('密码修改失败\nnewpwd: %s\ntext: %s', new_password, res)
            return False

    def set_telephone(self, tel):
        """
        更新电话

        @structure bool

        :param tel: 电话号码, 需要满足手机和普通电话的格式, 例如 `18112345678` 或者 '0791-1234567'
        """
        tel = six.text_type(tel)
        p = re.compile(r'^\d{11,12}$|^\d{4}-\d{7}$')
        if not p.match(tel):
            logger.warning('电话格式不匹配')
            return False

        method = 'post'
        url = 'student/asp/amend_tel.asp'
        data = {'tel': tel}
        response = self.api_request(method, url, data=data)

        page = response.text
        ss = SoupStrainer('input', attrs={'name': 'tel'})
        bs = BeautifulSoup(page, self.html_parser, parse_only=ss)
        return bs.input['value'] == tel

    # ========== 选课功能相关 ==========
    def get_optional_courses(self, kclx='x'):
        """
        获取可选课程, 并不判断是否选满

        @structure [{'学分': float, '开课院系': str, '课程代码': str, '课程名称': str, '课程类型': str}]

        :param kclx: 课程类型参数,只有三个值,{x:全校公选课, b:全校必修课, jh:本专业计划},默认为'x'
        """
        if kclx not in ('x', 'b', 'jh'):
            raise ValueError('kclx 参数不正确!')
        params = {'kclx': kclx}
        method = 'get'
        # url = 'student/asp/select_topLeft.asp'
        url = 'student/asp/select_topLeft_f3.asp'
        allow_redirects = False
        response = self.api_request(method, url, params=params, allow_redirects=allow_redirects)

        page = response.text
        ss = SoupStrainer('table', id='KCTable')
        bs = BeautifulSoup(page, self.html_parser, parse_only=ss)
        courses = []
        trs = bs.find_all('tr')
        value_list = [tuple(tr.stripped_strings) for tr in trs]
        for values in value_list:
            course = {'课程代码': values[0].upper(),
                      '课程名称': values[1],
                      '课程类型': values[2],
                      '开课院系': values[3],
                      '学分': float(values[4])}
            courses.append(course)
        return courses

    def get_selected_courses(self):
        """
        获取所有已选的课程

        @structure [{'费用': float, '教学班号': str, '课程名称': str, '课程代码': str, '学分': float, '课程类型': str}]
        """
        method = 'get'
        url = 'student/asp/select_down_f3.asp'
        allow_redirects = False
        response = self.api_request(method, url, allow_redirects=allow_redirects)

        page = response.text
        ss = SoupStrainer('table', id='TableXKJG')
        bs = BeautifulSoup(page, self.html_parser, parse_only=ss)

        courses = []
        keys = tuple(bs.find('tr', bgcolor='#296DBD').stripped_strings)
        # value_list = [tr.stripped_strings for tr in bs.find_all('tr', bgcolor='#D6D3CE')]
        value_list = parse_tr_strs(bs.find_all('tr', bgcolor='#D6D3CE'))
        for values in value_list:
            course = dict(safe_zip(keys, values))
            course['课程代码'] = course['课程代码'].upper()
            course['学分'] = float(course['学分'])
            course['费用'] = float(course['费用'])
            courses.append(course)
        return courses

    def change_course(self, select_courses=None, delete_courses=None):
        """
        修改个人的课程

        @structure [{'费用': float, '教学班号': str, '课程名称': str, '课程代码': str, '学分': float, '课程类型': str}]

        :param select_courses: 形如 ``{'kcdm': '9900039X', jxbhs: ['0001', '0002']}`` 的课程代码与教学班号列表, jxbhs 可以为空代表选择所有可选班级
        :param delete_courses: 需要删除的课程代码列表, 如 ``['0200011B']``
        :return: 选课结果, 返回选中的课程教学班列表, 结构与 ``get_selected_courses`` 一致
        """
        t = self.get_system_state()
        if t['当前轮数'] is None:
            raise ValueError('当前为 %s,选课系统尚未开启', t['当前学期'])
        if not (select_courses or delete_courses):
            raise ValueError('select_courses, delete_courses 参数不能都为空!')
        # 参数处理
        select_courses = select_courses or []
        delete_courses = {l.upper() for l in (delete_courses or [])}

        selected_courses = self.get_selected_courses()
        selected_kcdms = {course['课程代码'] for course in selected_courses}

        # 尝试删除没有被选中的课程会出错
        unselected = delete_courses.difference(selected_kcdms)
        if unselected:
            msg = '无法删除没有被选的课程 {}'.format(unselected)
            logger.error(msg)
            raise ValueError(msg)

        # 要提交的 kcdm 数据
        kcdms_data = []
        # 要提交的 jxbh 数据
        jxbhs_data = []

        # 必须添加已选课程, 同时去掉要删除的课程
        for course in selected_courses:
            if course['课程代码'] not in delete_courses:
                kcdms_data.append(course['课程代码'])
                jxbhs_data.append(course['教学班号'])

        # 选课
        for kv in select_courses:
            kcdm = kv['kcdm'].upper()
            jxbhs = set(kv['jxbhs']) if kv.get('jxbhs') else set()

            teaching_classes = self.get_course_classes(kcdm)
            if teaching_classes is None:
                logger.warning('课程[%s]没有可选班级', kcdm)
                continue

            # 反正是统一提交, 不需要判断是否已满
            optional_jxbhs = {c['教学班号'] for c in teaching_classes['可选班级']}
            if jxbhs:
                wrong_jxbhs = jxbhs.difference(optional_jxbhs)
                if wrong_jxbhs:
                    msg = '课程[{}]{}没有教学班号{}'.format(kcdm, teaching_classes['课程名称'], wrong_jxbhs)
                    logger.error(msg)
                    raise ValueError(msg)
            else:
                jxbhs = optional_jxbhs
            for jxbh in jxbhs:
                kcdms_data.append(kcdm)
                jxbhs_data.append(jxbh)

        method = 'post'
        url = 'student/asp/selectKC_submit_f3.asp'
        allow_redirects = False
        data = {'xh': self.account, 'kcdm': kcdms_data, 'jxbh': jxbhs_data}
        response = self.api_request(method, url, data=data, allow_redirects=allow_redirects)

        if response.status_code == 302:
            msg = '提交选课失败, 可能是身份验证过期或选课系统已关闭'
            logger.error(msg)
            raise ValueError(msg)
        else:
            page = response.text
            # 当选择同意课程的多个教学班时, 若已选中某个教学班, 再选择其他班数据库会出错,
            # 其他一些不可预料的原因也会导致数据库出错
            p = re.compile(r'(成功提交选课数据|容量已满,请选择其他教学班|已成功删除下列选课数据).+?'
                           r'课程代码:\s*([\dbBxX]+)[\s;&nbsp]*教学班号:\s*(\d{4})', re.DOTALL)
            r = p.findall(page)
            if not r:
                logger.warning('正则没有匹配到结果, 可能出现了一些状况')
                return []
            msg_results = []
            for g in r:
                logger.info(' '.join(g))
                msg_result = dict(msg=g[0], kcdm=g[1], jxbh=g[2])
                msg_results.append(msg_result)

        # 通过已选课程前后对比确定课程修改结果
        before_change = dict_list_2_tuple_set(selected_courses)
        after_change = dict_list_2_tuple_set(self.get_selected_courses())
        deleted = before_change.difference(after_change)
        selected = after_change.difference(before_change)
        result = {'删除课程': dict_list_2_tuple_set(deleted, reverse=True) or None,
                  '选中课程': dict_list_2_tuple_set(selected, reverse=True) or None}
        logger.debug(result)

        return result

    def get_unfinished_evaluation(self):
        """
        获取未完成的课程评价

        @structure [{'教学班号': str, '课程名称': str, '课程代码': str}]
        """
        method = 'get'
        url = 'student/asp/jxpglb.asp'
        response = self.api_request(method, url)
        page = response.text
        ss = SoupStrainer('table', width='600', bgcolor='#000000')
        bs = BeautifulSoup(page, self.html_parser, parse_only=ss)
        forms = bs.find_all('form')
        result = []
        for form in forms:
            values = tuple(form.stripped_strings)
            if len(values) > 3:
                continue
            status = dict(zip(('课程代码', '课程名称', '教学班号'), values))
            result.append(status)
        return result

    def evaluate_course(self, kcdm, jxbh,
                        r101=1, r102=1, r103=1, r104=1, r105=1, r106=1, r107=1, r108=1, r109=1,
                        r201=3, r202=3, advice=''):
        """
        课程评价, 数值为 1-5, r1 类选项 1 为最好, 5 为最差, r2 类选项程度由深到浅, 3 为最好.

        默认都是最好的选项

        :param kcdm: 课程代码
        :param jxbh: 教学班号
        :param r101: 教学态度认真，课前准备充分
        :param r102: 教授内容充实，要点重点突出
        :param r103: 理论联系实际，反映最新成果
        :param r104: 教学方法灵活，师生互动得当
        :param r105: 运用现代技术，教学手段多样
        :param r106: 注重因材施教，加强能力培养
        :param r107: 严格要求管理，关心爱护学生
        :param r108: 处处为人师表，注重教书育人
        :param r109: 教学综合效果
        :param r201: 课程内容
        :param r202: 课程负担
        :param advice: 其他建议，不能超过120字且不能使用分号,单引号,都好
        :return:
        """
        advice_length = len(advice)

        if advice_length > 120 or re.search(r"[;']", advice):
            raise ValueError('advice 不能超过120字且不能使用分号和单引号')

        method = 'post'
        url = 'student/asp/Jxpg_2.asp'
        value_map = ['01', '02', '03', '04', '05']
        data = {
            'kcdm': kcdm,
            'jxbh': jxbh,
            'r101': value_map[r101 - 1],
            'r102': value_map[r102 - 1],
            'r103': value_map[r103 - 1],
            'r104': value_map[r104 - 1],
            'r105': value_map[r105 - 1],
            'r106': value_map[r106 - 1],
            'r107': value_map[r107 - 1],
            'r108': value_map[r108 - 1],
            'r109': value_map[r109 - 1],
            'r201': value_map[r201 - 1],
            'r202': value_map[r202 - 1],
            'txt13': advice
            # 可以不填
            # 'Maxtxt13': 120 - advice_length
        }
        response = self.api_request(method, url, data=data)
        if re.search('您已经成功提交', response.text):
            return True
        else:
            return False

    # ---------- 不需要专门的请求 ----------
    def check_courses(self, kcdms):
        """
        检查课程是否被选

        @structure [bool]

        :param kcdms: 课程代码列表
        :return: 与课程代码列表长度一致的布尔值列表, 已为True,未选为False
        """
        selected_courses = self.get_selected_courses()
        selected_kcdms = {course['课程代码'] for course in selected_courses}
        result = [True if kcdm in selected_kcdms else False for kcdm in kcdms]
        return result

    def get_selectable_courses(self, kcdms=None, dump_result=True, filename='可选课程.json', encoding='utf-8'):
        """
        获取所有能够选上的课程的课程班级, 注意这个方法遍历所给出的课程和它们的可选班级, 当选中人数大于等于课程容量时表示不可选.

        由于请求非常耗时且一般情况下用不到, 因此默认推荐在第一轮选课结束后到第三轮选课结束之前的时间段使用, 如果你仍然坚持使用, 你将会得到一个警告.

        @structure [{'可选班级': [{'起止周': str, '考核类型': str, '教学班附加信息': str, '课程容量': int, '选中人数': int,
         '教学班号': str, '禁选专业': str, '教师': [str], '校区': str, '优选范围': [str], '开课时间,开课地点': [str]}],
        '课程代码': str, '课程名称': str}]

        :param kcdms: 课程代码列表, 默认为所有可选课程的课程代码
        :param dump_result: 是否保存结果到本地
        :param filename: 保存的文件路径
        :param encoding: 文件编码
        """
        now = time.time()
        t = self.get_system_state()
        if not (t['选课计划'][0][1] < now < t['选课计划'][2][1]):
            logger.warning('只推荐在第一轮选课结束到第三轮选课结束之间的时间段使用本接口!')

        kcdms = kcdms or [l['课程代码'] for l in self.get_optional_courses()]
        result = []

        def target(kcdm):
            course_classes = self.get_course_classes(kcdm)
            if course_classes is not None:
                course_classes['可选班级'] = [c for c in course_classes['可选班级'] if c['课程容量'] > c['选中人数']]
                if len(course_classes['可选班级']) > 0:
                    # http://stackoverflow.com/questions/6319207/are-lists-thread-safe
                    result.append(course_classes)

        threads = (Thread(target=target, args=(kcdm,), name=kcdm) for kcdm in kcdms)
        for t in threads:
            t.start()

        for t in threads:
            t.join()

        if dump_result:
            json_str = json.dumps(result, ensure_ascii=False, indent=4, sort_keys=True)
            with open(filename, 'wb') as fp:
                fp.write(json_str.encode(encoding))
            logger.debug('可选课程结果导出到了:%s', filename)
        return result
