# -*- coding:utf-8 -*-
"""
hfut_stu_lib 核心的模块, 包括了 :class:`models.APIResult` 和包含各个接口的各个 ``Session`` 类, 继承关系如下:

:class:`requests.sessions.Session` ->
:class:`models.BaseSession` ->
:class:`models.GuestSession` ->
:class:`models.AuthSession` ->
:class:`models.StudentSession`

"""
from __future__ import unicode_literals, division
import os
import re
import six
import json
import time
import requests
from bs4 import SoupStrainer, BeautifulSoup

from .log import logger
from .parser import parse_tr_strs, flatten_list, dict_list_2_tuple_set, parse_course

__all__ = ['APIResult', 'BaseSession', 'GuestSession', 'AuthSession', 'StudentSession', 'ADMIN', 'STUDENT', 'TEACHER']

ADMIN = 'admin'
STUDENT = 'student'
TEACHER = 'teacher'


@six.python_2_unicode_compatible
class APIResult(object):
    """
    所有接口返回数据的封装
    """

    def __init__(self, data=None, response=None):
        """
        :param data: 接口返回的数据
        :type response: :class:`requests.Response`
        """
        super(APIResult, self).__init__()
        self.response = response
        self.data = data

    def json(self):
        """
        将数据转换为 json 字符串
        """
        return json.dumps(self.data, ensure_ascii=False, sort_keys=True)

    def store_api_result(self, basename=None, dir_path=None, encoding='utf-8'):
        """
        如果有的话, 将请求对象的数据和响应内容保存在本地

        :param basename: 保存的不带后缀的文件名, 默认为 `api_result`
        :param dir_path: 保存的文件夹
        :param encoding: 文件编码
        """
        basename = basename or 'api_result'
        filename = os.path.join(dir_path, basename)
        if self.response:
            with open(filename + '.html', 'wb') as fp:
                fp.write(self.response.text.encode(encoding))
        json_str = json.dumps(self.data, ensure_ascii=False, indent=4, sort_keys=True)
        with open(filename + '.json', 'wb') as fp:
            fp.write(json_str.encode(encoding))

    def __str__(self):
        if self.response:
            request = self.response.request
            return '<APIResult> [{:s}] {:s}'.format(request.method, request.url)
        return '<APIResult> without response'

    def __iter__(self):
        return self.data.__iter__()

    def __getitem__(self, item):
        return self.data.__getitem__(item)

    def __getattr__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]
        else:
            return self.data.__getattribute__(item)

    def __len__(self):
        return self.data.__len__()

    def __bool__(self):
        return self.data.__bool__()


class BaseSession(requests.Session):
    """
    所有接口会话类的基类
    """
    host = 'http://222.195.8.201/'
    site_encoding = 'gbk'
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/45.0.2454.101 Safari/537.36'
    }
    html_parser = 'html.parser'

    def api_request(self, method, url, params=None, data=None, headers=None, cookies=None, files=None, auth=None,
                    timeout=None, allow_redirects=True, proxies=None, hooks=None, stream=None, verify=None, cert=None,
                    json=None):
        """
        所有接口用来发送请求的方法, 只是 :meth:`requests.sessions.Session.request` 的一个钩子方法, 用来处理请求前后的工作

        :param url: 教务系统页面的相对地址
        """
        if not six.moves.urllib.parse.urlparse(url).netloc:
            url = six.moves.urllib.parse.urljoin(self.host, url)
        response = self.request(method, url, params=params, data=data, headers=headers, cookies=cookies, files=files,
                                auth=auth, timeout=timeout, allow_redirects=allow_redirects, proxies=proxies,
                                hooks=hooks, stream=stream, verify=verify, cert=cert, json=json)
        response.encoding = self.site_encoding
        logger.debug('[%s] %s 请求成功,请求耗时 %d ms', method, url, response.elapsed.total_seconds() * 1000)
        return response

    def __init__(self):
        # todo: 初始化时根据合肥选择不同的地址
        super(BaseSession, self).__init__()
        self.headers = self.default_headers


class GuestSession(BaseSession):
    """
    无需登录就可使用的接口
    """

    def get_system_state(self):
        """
        获取教务系统当前状态信息, 包括当前学期以及选课计划
        """
        method = 'get'
        url = 'student/asp/s_welcome.asp'
        response = self.api_request(method, url)
        # 学期后有一个 </br> 便签, html.parser 会私自的将它替换为 </table> 导致无获取后面的 html
        # ss = SoupStrainer('table', height='85%')
        bs = BeautifulSoup(response.text, self.html_parser)
        text = bs.get_text(strip=True)
        term_pattern = re.compile(r'现在是\d{4}-\d{4}学年第(一|二)学期')
        term = term_pattern.search(text).group()
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

        logger.debug(result)
        return APIResult(result, response)

    def get_class_students(self, xqdm, kcdm, jxbh):
        """
        教学班查询, 查询指定教学班的所有学生

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
        term_p = r'\d{4}-\d{4}学年第(一|二)学期'
        term = re.search(term_p, page)
        class_name_p = r'[\u4e00-\u9fa5\w-]+\d{4}班'
        class_name = re.search(class_name_p, page)
        # 虽然 \S 能解决匹配失败中文的问题, 但是最后的结果还是乱码的
        stu_p = r'>\s*?(\d{1,3})\s*?</.*?>\s*?(\d{10})\s*?</.*?>\s*?([\u4e00-\u9fa5*]+)\s*?</'
        stus = re.findall(stu_p, page, re.DOTALL)
        if term and class_name and stus:
            stus = [{'序号': v[0], '学号': v[1], '姓名': v[2]} for v in stus]
            return APIResult({'学期': term.group(), '班级名称': class_name.group(), '学生': stus}, response)
        elif page.find('无此教学班') != -1:
            logger.warning('无此教学班, 请检查你的参数')
            return APIResult(response=response)
        else:
            msg = '\n'.join(['没有匹配到信息, 可能出现了一些问题', page])
            logger.error(msg)
            raise ValueError(msg)

    def get_class_info(self, xqdm, kcdm, jxbh):
        """
        获取教学班详情, 包括上课时间地点, 考查方式, 老师, 选中人数, 课程容量等等信息

        :param xqdm: 学期代码
        :param kcdm: 课程代码
        :param jxbh: 教学班号
        """
        method = 'get'
        url = 'student/asp/xqkb1_1.asp'
        params = {'xqdm': xqdm,
                  'kcdm': kcdm.upper(),
                  'jxbh': jxbh}
        response = self.api_request(method, url, params)

        page = response.text
        ss = SoupStrainer('table', width='600')
        bs = BeautifulSoup(page, self.html_parser, parse_only=ss)
        # 有三行 , 教学班号	课程名称	课程类型	学分  开课单位	校区	起止周	考核类型  性别限制	选中人数
        key_list = [list(tr.stripped_strings) for tr in bs.find_all('tr', bgcolor='#B4B9B9')]
        assert len(key_list) == 3
        # 有7行, 前三行与 key_list 对应, 后四行是单行属性, 键与值在同一行
        trs = bs.find_all('tr', bgcolor='#D6D3CE')
        # 最后的 备注, 禁选范围 两行外面包裹了一个 'tr' bgcolor='#D6D3CE' 时间地点 ......
        # 如果使用 lxml 作为解析器, 会自动纠正错误
        # 前三行, 注意 value_list 第三行是有两个单元格为 None,
        value_list = parse_tr_strs(trs[:3])
        # Python3 的 map 返回的是生成器, 不会立即产生结果
        # map(lambda seq: class_info.update(dict(zip(seq[0], seq[1]))), zip(key_list, value_list))
        class_info = {k: v for k, v in zip(flatten_list(key_list), flatten_list(value_list))}
        # 后四行
        last_4_lines = [list(tr.stripped_strings) for tr in trs[3:7]]
        last_4_lines[1] = last_4_lines[1][:-(len(last_4_lines[2]) + len(last_4_lines[3]))]
        for kv in last_4_lines:
            k = kv[0]
            v = None if len(kv) == 1 else kv[1]
            class_info[k] = v
        return APIResult(class_info, response)

    def search_course(self, xqdm, kcdm=None, kcmc=None):
        """
        课程查询

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
            value_list = [tr.stripped_strings for tr in trs]
            for values in value_list:
                course = dict(zip(keys, values))
                course['课程代码'] = course['课程代码'].upper()
                courses.append(course)
            return APIResult(courses, response)
        else:
            logger.warning('没有找到结果\n %s', data)
            return APIResult(response=response)

    def get_teaching_plan(self, xqdm, zydm, kclx='b'):
        """
        专业教学计划查询

        :param xqdm: 学期代码
        :param kclx: 课程类型参数,只有两个值 b:专业必修课, x:全校公选课
        :param zydm: 专业代码, 可以从 :meth:`models.StudentSession.get_code` 获得
        """
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
        value_list = [tr.stripped_strings for tr in trs[2:]]
        teaching_plan = []
        for values in value_list:
            plan = dict(zip(keys, values))
            plan['课程代码'] = plan['课程代码'].upper()
            teaching_plan.append(plan)
        return APIResult(teaching_plan, response)

    def get_teacher_info(self, jsh):
        """
        教师信息查询

        :param jsh: 8位教师号, 例如 '05000162'
        """
        params = {'jsh': jsh}
        method = 'get'
        url = 'teacher/asp/teacher_info.asp'
        response = self.api_request(method, url, params)

        page = response.text
        ss = SoupStrainer('table')
        bs = BeautifulSoup(page, self.html_parser, parse_only=ss)

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
        return APIResult(teacher_info, response)

    def get_course_classes(self, kcdm):
        """
        获取选课系统中课程的可选教学班级

        :param kcdm: 课程代码
        """
        params = {'kcdm': kcdm.upper()}
        method = 'get'
        # url = 'student/asp/select_topRight.asp'
        url = 'student/asp/select_topRight_f3.asp'
        response = self.api_request(method, url, params)

        page = response.text
        ss = SoupStrainer('body')
        bs = BeautifulSoup(page, self.html_parser, parse_only=ss)
        class_table = bs.select_one('#JXBTable')
        if class_table.get_text(strip=True) == '对不起！该课程没有可被选的教学班。':
            return APIResult(None, response)

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
            cls_info = dict(zip(info_trs[0].stripped_strings, parse_tr_strs([info_trs[1]])))
            # 选中人数 课程容量
            for s in info_trs[2].stripped_strings:
                kv = [v.strip() for v in s.split(':')]
                cls_info[kv[0]] = int(kv[1]) if kv[1] else None
            cls_info.update([(v.strip() or None for v in s.split('：')) for s in info_trs[5].stripped_strings])
            # 开课时间,开课地点
            p = re.compile(r'周[一二三四五六日]:\(\d+-\d+节\) \(\d+-\d+周\).+?\d+')
            cls_info[info_trs[3].get_text(strip=True)] = p.findall(info_trs[4].get_text(strip=True))

            cls_info['教学班号'] = tds[1].string.strip()
            cls_info['教师'] = [s.strip() for s in tds[2].text.split(',')]
            cls_info['优选范围'] = [s.strip() for s in tds[3].text.split(',')]

            course_classes.append(cls_info)

        result['可选班级'] = course_classes
        return APIResult(result, response)

    def get_entire_curriculum(self, xqdm):
        """
        获取全校的学期课程表

        :param xqdm: 学期代码
        """
        method = 'get'
        url = 'teacher/asp/Jskb_table.asp'
        params = {'xqdm': xqdm}
        response = self.api_request(method, url, params)

        page = response.text
        ss = SoupStrainer('table', width='840')
        bs = BeautifulSoup(page, self.html_parser, parse_only=ss)
        trs = bs.find_all('tr')
        origin_list = parse_tr_strs(trs[1:])

        # 顺时针反转矩阵
        length = len(origin_list)
        width = len(origin_list[0])
        new_matrix = []
        #
        for i in range(width):
            newline = []
            for j in range(length):
                newline.append(parse_course(origin_list[j][i]))
            new_matrix.append(newline)

        # 去除第一行的序号
        timetable = new_matrix[1:]
        return APIResult(timetable, response)


@six.python_2_unicode_compatible
class AuthSession(GuestSession):
    """
    用于所有需要登录的用户角色继承的基类
    """

    def __init__(self, account, password, user_type):
        """
        :param account: 学号
        :param password: 密码
        """
        # 先初始化状态才能登陆
        super(AuthSession, self).__init__()
        self.account = account
        self.password = password
        self.user_type = user_type
        self.last_request_at = time.time()
        self.login_session()

    def __str__(self):
        return '<AuthSession for [{user_type}]{account}>'.format(account=self.account, user_type=self.user_type)

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

    def login_session(self):
        """
        登录账户
        """
        # todo: 实现合肥校区的登录
        account = self.account
        password = self.password
        user_type = self.user_type

        user_type = user_type.lower()
        assert (user_type in (STUDENT, ADMIN)) and all([account, password])

        method = 'post'
        url = 'pass.asp'
        allow_redirects = False
        data = {"user": account, "password": password, "UserStyle": user_type}

        # 使用重载的 api_request 会造成递归调用
        response = super(AuthSession, self).api_request(method, url, data=data, allow_redirects=allow_redirects)
        logged_in = response.status_code == 302
        if not logged_in:
            if 'SQL通用防注入系统' in response.text:
                msg = '当前 IP 已被锁定,如果是宣城校内访问请切换教务系统地址,否则请在更换网络环境后重试'
                logger.warning(msg)
            else:
                msg = '登陆失败, 请检查你的账号和密码'
                logger.error(msg)
            raise ValueError(msg)

        # if user_type == STUDENT:
        #     escaped_name = self.cookies.get('xsxm')
        # else:
        #     escaped_name = None
        # self.name = six.moves.urllib.parse.unquote(escaped_name, self.site_encoding)

        result = APIResult(logged_in, response)
        return result

    def api_request(self, method, url, params=None, data=None, headers=None, cookies=None, files=None, auth=None,
                    timeout=None, allow_redirects=True, proxies=None, hooks=None, stream=None, verify=None, cert=None,
                    json=None):

        if self.is_expired:
            self.login_session()
        self.last_request_at = time.time()

        return super(AuthSession, self).api_request(
            method, url, params=params, data=data, headers=headers, cookies=cookies,
            files=files, auth=auth, timeout=timeout, allow_redirects=allow_redirects,
            proxies=proxies, hooks=hooks, stream=stream, verify=verify, cert=cert, json=json
        )


@six.python_2_unicode_compatible
class StudentSession(AuthSession):
    """
    学生教务接口, 继承了 :class:`models.GuestSession` 的所有接口, 因此一般推荐使用这个类
    """

    def __init__(self, account, password):
        """
        :param account: 学号
        :param password: 账号密码
        """
        super(StudentSession, self).__init__(account, password, STUDENT)

    def __str__(self):
        return '<StudentSession for [{user_type}]{account}>'.format(account=self.account, user_type=self.user_type)

    def get_code(self):
        """
        获取当前所有的学期, 学期以及对应的学期代码, 注意如果你只是需要获取某个学期的代码的话请使用 :func:`util.cal_term_code`
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

        return APIResult(result, response)

    def get_my_info(self):
        """
        获取个人信息
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
            kv_tuple = (v.strip() for v in cell.split(':'))
            kvs.append(kv_tuple)
        stu_info.update(kvs)

        # 解析后面对应的信息
        for line in zip(key_lines, value_lines[2:]):
            stu_info.update(zip(line[0], line[1]))

        # 添加照片项
        photo_url = six.moves.urllib.parse.urljoin(response.url, bs.select_one('td[rowspan=6] img')['src'])
        stu_info['照片'] = photo_url

        return APIResult(stu_info, response)

    def get_my_achievements(self):
        """
        获取个人成绩
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
            grade = dict(zip(keys, values))
            grade['课程代码'] = grade['课程代码'].upper()
            grades.append(grade)
        return APIResult(grades, response)

    def get_my_curriculum(self):
        """
        获取个人课表
        """
        method = 'get'
        url = 'student/asp/grkb1.asp'
        response = self.api_request(method, url)

        page = response.text
        ss = SoupStrainer('table', width='840')
        bs = BeautifulSoup(page, self.html_parser, parse_only=ss)
        trs = bs.find_all('tr')
        origin_list = parse_tr_strs(trs[1:])

        # 顺时针反转矩阵
        length = len(origin_list)
        width = len(origin_list[0])
        new_matrix = []
        for i in range(width):
            newline = []
            for j in range(length):
                newline.append(parse_course(origin_list[j][i]))
            new_matrix.append(newline)

        # 去除第一行的序号
        timetable = new_matrix[1:]
        return APIResult(timetable, response)

    def get_my_fees(self):
        """
        收费查询
        """
        method = 'get'
        url = 'student/asp/Xfsf_Count.asp'
        response = self.api_request(method, url)

        page = response.text
        ss = SoupStrainer('table', bgcolor='#000000')
        bs = BeautifulSoup(page, self.html_parser, parse_only=ss)

        keys = tuple(bs.table.thead.tr.stripped_strings)
        value_trs = bs.find_all('tr', bgcolor='#D6D3CE')
        value_list = [tr.stripped_strings for tr in value_trs]
        feeds = []
        for values in value_list:
            feed = dict(zip(keys, values))
            feed['课程代码'] = feed['课程代码'].upper()
            feeds.append(feed)
        return APIResult(feeds, response)

    def change_password(self, oldpwd, newpwd, new2pwd):
        """
        修改密码

        :param self: AuthSession 对象
        :param oldpwd: 旧密码
        :param newpwd: 新密码
        :param new2pwd: 重复新密码
        """
        p = re.compile(r'^[\da-z]{6,12}$')
        # 若不满足密码修改条件便不做请求
        if oldpwd != self.password or newpwd != new2pwd or not p.match(newpwd):
            return APIResult(False)
        # 若新密码与原密码相同, 直接返回 True
        if newpwd == oldpwd:
            return APIResult(True)

        method = 'post'
        url = 'student/asp/amend_password_jg.asp'
        data = {'oldpwd': oldpwd,
                'newpwd': newpwd,
                'new2pwd': new2pwd}
        response = self.api_request(method, url, data=data)

        page = response.text
        ss = SoupStrainer('table', width='580', border='0', cellspacing='1', bgcolor='#000000')
        bs = BeautifulSoup(page, self.html_parser, parse_only=ss)
        res = bs.text.strip()
        if res == '密码修改成功！':
            self.password = newpwd
            return APIResult(True, response)
        else:
            logger.warning('密码修改失败\noldpwd: %s\nnewpwd: %s\nnew2pwd: %s\ntext: %s', oldpwd, newpwd, new2pwd, res)
            return APIResult(False, response)

    def set_telephone(self, tel):
        """
        更新电话

        :param tel: 电话号码, 需要满足手机和普通电话的格式, 例如 `18112345678` 或者 '0791-1234567'
        """
        tel = six.text_type(tel)
        p = re.compile(r'^\d{11,12}$|^\d{4}-\d{7}$')
        if not p.match(tel):
            logger.warning('电话格式不匹配')
            return APIResult(False)

        method = 'post'
        url = 'student/asp/amend_tel.asp'
        data = {'tel': tel}
        response = self.api_request(method, url, data=data)

        page = response.text
        ss = SoupStrainer('input', attrs={'name': 'tel'})
        bs = BeautifulSoup(page, self.html_parser, parse_only=ss)
        return APIResult(bs.input['value'] == tel, response)

    # ========== 选课功能相关 ==========
    def get_optional_courses(self, kclx='x'):
        """
        获取可选课程, 并不判断是否选满

        :param kclx: 课程类型参数,只有三个值,{x:全校公选课, b:全校必修课, jh:本专业计划},默认为'x'
        """
        if kclx not in ('x', 'b', 'jh'):
            raise ValueError('kclx 参数不正确!')
        params = {'kclx': kclx}
        method = 'get'
        # url = 'student/asp/select_topLeft.asp'
        url = 'student/asp/select_topLeft_f3.asp'
        allow_redirects = False
        response = self.api_request(method, url, params, allow_redirects=allow_redirects)

        page = response.text
        ss = SoupStrainer('table', id='KCTable')
        bs = BeautifulSoup(page, self.html_parser, parse_only=ss)
        courses = []
        trs = bs.find_all('tr')
        value_list = [tuple(tr.stripped_strings) for tr in trs[:-1]]
        for values in value_list:
            course = {'课程代码': values[0].upper(),
                      '课程名称': values[1],
                      '课程类型': values[2],
                      '开课院系': values[3],
                      '学分': values[4]}
            courses.append(course)
        return APIResult(courses, response)

    def get_selected_courses(self):
        """
        获取所有已选的课程
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
        value_list = [tr.stripped_strings for tr in bs.find_all('tr', bgcolor='#D6D3CE')]
        for values in value_list:
            course = dict(zip(keys, values))
            course['课程代码'] = course['课程代码'].upper()
            course['学分'] = float(course['学分'])
            course['费用'] = int(course['费用'])
            courses.append(course)
        return APIResult(courses, response)

    def change_course(self, select_courses=None, delete_courses=None):
        """
        修改个人的课程

        :param select_courses: 形如 ``{'kcdm': '9900039X', jxbhs: ['0001', '0002']}`` 的课程代码与教学班号列表, jxbhs 可以为空代表选择所有可选班级
        :param delete_courses: 需要删除的课程代码列表, 如 ``['0200011B']``
        :return: 选课结果, 返回选中的课程教学班列表
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
                return APIResult(response=response)
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

        return APIResult(result, response)

    # ---------- 不需要专门的请求 ----------
    def check_courses(self, kcdms):
        """
        检查课程是否被选

        :param kcdms: 课程代码列表
        :return: 与课程代码列表长度一致的布尔值列表, 已为True,未选为False
        """
        selected_courses = self.get_selected_courses()
        selected_kcdms = {course['课程代码'] for course in selected_courses}
        result = [True if kcdm in selected_kcdms else False for kcdm in kcdms]
        return APIResult(result)

    def get_selectable_courses(self, kcdms=None, dump_result=True, filename='可选课程.json', encoding='utf-8'):
        """
        获取所有能够选上的课程的课程班级, 注意这个方法遍历所给出的课程和它们的可选班级, 当选中人数大于等于课程容量时表示不可选.

        由于请求非常耗时且一般情况下用不到, 因此默认推荐在第一轮选课结束后到第三轮选课结束之前的时间段使用, 如果你仍然坚持使用, 你将会得到一个警告.

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
        for kcdm in kcdms:
            course_classes = self.get_course_classes(kcdm).data
            if course_classes is not None:
                course_classes['可选班级'] = [c for c in course_classes['可选班级'] if c['课程容量'] > c['选中人数']]
                if len(course_classes['可选班级']) > 0:
                    result.append(course_classes)
        if dump_result:
            json_str = json.dumps(result, ensure_ascii=False, indent=4, sort_keys=True)
            with open(filename + '.json', 'wb') as fp:
                fp.write(json_str.encode(encoding))
            logger.debug('result dumped to %s', filename)
        return APIResult(result)
