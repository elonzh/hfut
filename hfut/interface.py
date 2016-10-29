# -*- coding:utf-8 -*-
from __future__ import unicode_literals, division

import re
import time
from copy import deepcopy

import six
from bs4 import BeautifulSoup, SoupStrainer
from requests import Request

from .log import logger, log_result_not_found
from .parser import parse_tr_strs, flatten_list, parse_course, safe_zip
from .session import BaseSession, StudentSession
from .value import HTML_PARSER, SITE_ENCODING, TERM_PATTERN, XC_PASSWORD_PATTERN

__all__ = [
    'BaseInterface', 'GetSystemStatus', 'GetClassStudents', 'GetClassInfo', 'SearchCourse', 'GetTeachingPlan',
    'GetTeacherInfo', 'GetCourseClasses', 'GetEntireCurriculum',
    'GetCode', 'GetMyInfo', 'GetMyAchievements', 'GetMyCurriculum', 'GetMyFees', 'ChangePassword', 'SetTelephone',
    'GetOptionalCourses', 'GetSelectedCourses', 'ChangeCourse', 'GetUnfinishedEvaluation', 'EvaluateCourse'
]


class BaseInterface(object):
    """
    所有接口的类的基类, 所有的接口都必须继承这个类.

    所有的接口都要实现方法 ``__init__`` 用来初始化 ``self.session`` 和 ``self.extra_kwargs``, 必须在所有的实现前调用基类的方法.

    所有的接口都要实现方法 ``parse`` 用来将响应解析为规格化的结果.
    """
    session_class = NotImplemented
    request_kwargs = {
        'method': NotImplemented, 'url': NotImplemented
    }
    extra_kwargs = {}
    # {'proxies': None, 'stream': None, 'verify': None, 'cert': None,'timeout': None, 'allow_redirects': True}
    send_kwargs = {}

    def parse(self, response):
        raise NotImplemented('你需要实现对响应的解析过程')

    def make_request(self):
        kwargs = deepcopy(self.request_kwargs)
        kwargs.update(self.extra_kwargs)
        req = Request(**kwargs)
        return req


class GetSystemStatus(BaseInterface):
    session_class = (BaseSession, StudentSession)
    request_kwargs = {
        'method': 'get',
        'url': 'student/asp/s_welcome.asp'
    }

    def parse(self, response):
        # 学期后有一个 </br> 便签, html.parser 会私自的将它替换为 </table> 导致无获取后面的 html
        # ss = SoupStrainer('table', height='85%')
        bs = BeautifulSoup(response.text, HTML_PARSER)
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


class GetClassStudents(BaseInterface):
    session_class = (BaseSession, StudentSession)
    request_kwargs = {
        'method': 'get',
        'url': 'student/asp/Jxbmdcx_1.asp'
    }

    def __init__(self, xqdm, kcdm, jxbh):
        self.extra_kwargs['params'] = {
            'xqdm': xqdm,
            'kcdm': kcdm.upper(),
            'jxbh': jxbh
        }

    def parse(self, response):
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


class GetClassInfo(BaseInterface):
    session_class = (BaseSession, StudentSession)
    request_kwargs = {
        'method': 'get',
        'url': 'student/asp/xqkb1_1.asp'
    }

    def __init__(self, xqdm, kcdm, jxbh):
        self.extra_kwargs['params'] = {
            'xqdm': xqdm,
            'kcdm': kcdm.upper(),
            'jxbh': jxbh
        }

    def parse(self, response):
        page = response.text
        ss = SoupStrainer('table', width='600')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)
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


class SearchCourse(BaseInterface):
    session_class = (BaseSession, StudentSession)
    request_kwargs = {
        'method': 'post',
        'url': 'student/asp/xqkb1.asp'
    }

    def __init__(self, xqdm, kcdm=None, kcmc=None):
        if kcdm is None and kcmc is None:
            raise ValueError('kcdm 和 kcdm 参数必须至少存在一个')
        self.extra_kwargs['data'] = {
            'xqdm': xqdm,
            'kcdm': kcdm.upper() if kcdm else None,
            'kcmc': kcmc.encode(SITE_ENCODING) if kcmc else None
        }

    def parse(self, response):
        page = response.text
        ss = SoupStrainer('table', width='650')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)
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


class GetTeachingPlan(BaseInterface):
    session_class = (BaseSession, StudentSession)
    request_kwargs = {
        'method': 'post',
        'url': 'student/asp/xqkb2.asp'
    }

    def __init__(self, xqdm, kclx='b', zydm=''):
        if kclx == 'b' and not zydm:
            raise ValueError('查询专业必修课必须提供专业代码')
        kclxdm = {'b': 1, 'x': 3}[kclx]
        self.extra_kwargs['data'] = {
            'xqdm': xqdm,
            'kclxdm': kclxdm,
            'ccjbyxzy': zydm
        }

    def parse(self, response):
        page = response.text
        ss = SoupStrainer('table', width='650')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)
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


class GetTeacherInfo(BaseInterface):
    session_class = (BaseSession, StudentSession)
    request_kwargs = {
        'method': 'get',
        'url': 'teacher/asp/teacher_info.asp'
    }

    def __init__(self, jsh):
        self.extra_kwargs['params'] = {'jsh': jsh}

    def parse(self, response):
        page = response.text
        ss = SoupStrainer('table')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)
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


class GetCourseClasses(BaseInterface):
    session_class = (BaseSession, StudentSession)
    request_kwargs = {
        'method': 'get',
        # 'student/asp/select_topRight.asp'
        'url': 'student/asp/select_topRight_f3.asp'
    }

    def __init__(self, kcdm):
        self.extra_kwargs['params'] = {'kcdm': kcdm.upper()}

    def parse(self, response):
        page = response.text
        ss = SoupStrainer('body')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)
        class_table = bs.select_one('#JXBTable')
        if class_table.get_text(strip=True) == '对不起！该课程没有可被选的教学班。':
            log_result_not_found(page)
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
            class_info_table = BeautifulSoup(tds[1]['alt'], HTML_PARSER)
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


class GetEntireCurriculum(BaseInterface):
    session_class = (BaseSession, StudentSession)
    request_kwargs = {
        'method': 'get',
        'url': 'teacher/asp/Jskb_table.asp'
    }

    def __init__(self, xqdm=None):
        self.extra_kwargs['params'] = {'xqdm': xqdm}

    def parse(self, response):
        page = response.text
        ss = SoupStrainer('table', width='840')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)
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


class GetCode(BaseInterface):
    session_class = StudentSession
    request_kwargs = {
        'method': 'get',
        'url': 'student/asp/xqjh.asp'
    }

    def parse(self, response):
        page = response.text
        ss = SoupStrainer('select')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)
        xqdm_options = bs.find('select', attrs={'name': 'xqdm'}).find_all('option')
        xqdm = [{'学期代码': node['value'], '学期名称': node.string.strip()} for node in xqdm_options]
        ccjbyxzy_options = bs.find('select', attrs={'name': 'ccjbyxzy'}).find_all('option')
        ccjbyxzy = [{'专业代码': node['value'], '专业名称': node.string.strip()} for node in ccjbyxzy_options]
        result = {'学期': xqdm, '专业': ccjbyxzy}
        return result


class GetMyInfo(BaseInterface):
    session_class = StudentSession
    request_kwargs = {
        'method': 'get',
        'url': 'student/asp/xsxxxxx.asp'
    }

    def parse(self, response):
        page = response.text
        ss = SoupStrainer('table')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)

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


class GetMyAchievements(BaseInterface):
    session_class = StudentSession
    request_kwargs = {
        'method': 'get',
        'url': 'student/asp/Select_Success.asp'
    }

    def parse(self, response):
        page = response.text
        ss = SoupStrainer('table', width='582')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)
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


class GetMyCurriculum(BaseInterface):
    session_class = StudentSession
    request_kwargs = {
        'method': 'get',
        'url': 'student/asp/grkb1.asp'
    }

    def parse(self, response):
        page = response.text
        ss = SoupStrainer('table', width='840')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)
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


class GetMyFees(BaseInterface):
    session_class = StudentSession
    request_kwargs = {
        'method': 'get',
        'url': 'student/asp/Xfsf_Count.asp'
    }

    def parse(self, response):
        page = response.text
        ss = SoupStrainer('table', bgcolor='#000000')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)

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


class ChangePassword(BaseInterface):
    session_class = StudentSession
    request_kwargs = {
        'method': 'post',
        'url': 'student/asp/amend_password_jg.asp'
    }

    def __init__(self, password, new_password):
        # 若不满足密码修改条件便不做请求
        if not XC_PASSWORD_PATTERN.match(new_password):
            raise ValueError('密码为6-12位小写字母或数字')

        self.extra_kwargs['data'] = {
            'oldpwd': password,
            'newpwd': new_password,
            'new2pwd': new_password
        }
        self.new_password = new_password

    def parse(self, response):
        page = response.text
        ss = SoupStrainer('table', width='580', border='0', cellspacing='1', bgcolor='#000000')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)
        res = bs.text.strip()
        if res == '密码修改成功！':
            return True
        else:
            logger.warning('密码修改失败\nnewpwd: %s\ntext: %s', self.new_password, res)
            return False


class SetTelephone(BaseInterface):
    session_class = StudentSession
    request_kwargs = {
        'method': 'post',
        'url': 'student/asp/amend_tel.asp'
    }

    def __init__(self, tel):
        tel = six.text_type(tel)
        p = re.compile(r'^\d{11,12}$|^\d{4}-\d{7}$')
        if not p.match(tel):
            raise ValueError('电话格式不匹配')

        self.extra_kwargs['data'] = {'tel': tel}

    def parse(self, response):
        page = response.text
        ss = SoupStrainer('input', attrs={'name': 'tel'})
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)
        return bs.input['value'] == self.extra_kwargs['data']['tel']


class GetUnfinishedEvaluation(BaseInterface):
    session_class = StudentSession
    request_kwargs = {
        'method': 'get',
        'url': 'student/asp/jxpglb.asp'
    }

    def parse(self, response):
        page = response.text
        ss = SoupStrainer('table', width='600', bgcolor='#000000')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)
        forms = bs.find_all('form')
        result = []
        for form in forms:
            values = tuple(form.stripped_strings)
            if len(values) > 3:
                continue
            status = dict(zip(('课程代码', '课程名称', '教学班号'), values))
            result.append(status)
        return result


class EvaluateCourse(BaseInterface):
    session_class = StudentSession
    request_kwargs = {
        'method': 'post',
        'url': 'student/asp/Jxpg_2.asp'
    }

    def __init__(self, kcdm, jxbh,
                 r101=1, r102=1, r103=1, r104=1, r105=1, r106=1, r107=1, r108=1, r109=1,
                 r201=3, r202=3, advice=''):
        advice_length = len(advice)

        if advice_length > 120 or re.search(r"[;']", advice):
            raise ValueError('advice 不能超过120字且不能使用分号和单引号')
        value_map = ['01', '02', '03', '04', '05']
        self.extra_kwargs['data'] = {
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

    def parse(self, response):
        if re.search('您已经成功提交', response.text):
            return True
        else:
            return False


# ========== 选课功能相关 ==========
class GetOptionalCourses(BaseInterface):
    session_class = StudentSession
    request_kwargs = {
        'method': 'get',
        'url': 'student/asp/select_topLeft_f3.asp'
    }
    send_kwargs = {
        'allow_redirects': False
    }

    def __init__(self, kclx='x'):
        if kclx not in ('x', 'b', 'jh'):
            raise ValueError('kclx 参数不正确!')
        self.extra_kwargs['params'] = {'kclx': kclx}

    def parse(self, response):
        page = response.text
        ss = SoupStrainer('table', id='KCTable')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)
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


class GetSelectedCourses(BaseInterface):
    session_class = StudentSession
    request_kwargs = {
        'method': 'get',
        'url': 'student/asp/select_down_f3.asp'
    }
    send_kwargs = {
        'allow_redirects': False
    }

    def parse(self, response):
        page = response.text
        ss = SoupStrainer('table', id='TableXKJG')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)

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


class ChangeCourse(BaseInterface):
    session_class = StudentSession
    request_kwargs = {
        'method': 'post',
        'url': 'student/asp/selectKC_submit_f3.asp'
    }
    send_kwargs = {
        'allow_redirects': False
    }

    def __init__(self, account, kcdms_data, jxbhs_data):
        self.extra_kwargs['data'] = {'xh': account, 'kcdm': kcdms_data, 'jxbh': jxbhs_data}

    def parse(self, response):
        if response.status_code == 302:
            msg = '提交选课失败, 可能是身份验证过期或选课系统已关闭'
            logger.error(msg)
            raise ValueError(msg)
        else:
            # 这里只是用作检查此方法是否稳定
            page = response.text
            # 当选择同意课程的多个教学班时, 若已选中某个教学班, 再选择其他班数据库会出错,
            # 其他一些不可预料的原因也会导致数据库出错
            p = re.compile(r'(成功提交选课数据|容量已满,请选择其他教学班|已成功删除下列选课数据).*?'
                           r'课程代码：.*?([\dbBxX]{8}).*?'
                           r'教学班号：.*?(\d{4})')
            text = BeautifulSoup(page, HTML_PARSER).get_text(strip=True)
            r = p.findall(text)
            if r:
                msg_results = []
                for g in r:
                    logger.info(' '.join(g))
                    msg_result = dict(msg=g[0], kcdm=g[1], jxbh=g[2])
                    msg_results.append(msg_result)
                    logger.debug(msg_results)
                # todo: 待充分测试
                return msg_results
            else:
                log_result_not_found(page)
                # 通过已选课程前后对比确定课程修改结果
                # before_change = dict_list_2_tuple_set(self.selected_courses)
                # after_change = dict_list_2_tuple_set(GetSelectedCourses().query())
                # deleted = before_change.difference(after_change)
                # selected = after_change.difference(before_change)
                # result = {'删除课程': dict_list_2_tuple_set(deleted, reverse=True) or [],
                #           '选中课程': dict_list_2_tuple_set(selected, reverse=True) or []}
                # return result
