# -*- coding:utf-8 -*-
"""
核心的请求对象构造类, 使用原始参数获取响应并解析出结果
"""
from __future__ import unicode_literals, print_function, division

import re

import six
from bs4 import SoupStrainer, BeautifulSoup

from .const import GET, POST, GUEST, STUDENT, HTML_PARSER
from .log import logger
from .model import APIRequestBuilder, APIResult
from .parser import parse_tr_strs, flatten_list


class GetClassStudent(APIRequestBuilder):
    user_type = GUEST

    method = GET
    url = 'student/asp/Jxbmdcx_1.asp'

    def __init__(self, xqdm, kcdm, jxbh):
        """
        教学班查询
        :param xqdm: 学期代码
        :param kcdm: 课程代码
        :param jxbh: 教学班号
        """
        self.params = {'xqdm': xqdm,
                       'kcdm': kcdm.upper(),
                       'jxbh': jxbh}

    def after_response(self, response, *args, **kwargs):
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
            return APIResult(response, {'学期': term.group(), '班级名称': class_name.group(), '学生': stus})
        elif page.find('无此教学班') != -1:
            logger.warning('无此教学班, 请检查你的参数')
            return APIResult(response)
        else:
            msg = '\n'.join(['没有匹配到信息, 可能出现了一些问题', page])
            logger.error(msg)
            raise ValueError(msg)


class GetClassInfo(APIRequestBuilder):
    user_type = GUEST

    method = GET
    url = 'student/asp/xqkb1_1.asp'

    def __init__(self, xqdm, kcdm, jxbh):
        """
        获取教学班详情
        :rtype : dict
        :param xqdm: 学期代码
        :param kcdm: 课程代码
        :param jxbh: 教学班号
        """
        self.params = {'xqdm': xqdm,
                       'kcdm': kcdm.upper(),
                       'jxbh': jxbh}

    def after_response(self, response, *args, **kwargs):
        page = response.text
        ss = SoupStrainer('table', width='600')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)
        # 有三行
        key_list = [list(tr.stripped_strings) for tr in bs.find_all('tr', bgcolor='#B4B9B9')]
        assert len(key_list) == 3
        # 有六行, 前三行与 key_list 对应, 后四行是单行属性, 键与值在同一行
        trs = bs.find_all('tr', bgcolor='#D6D3CE')
        # 最后的 备注, 禁选范围 两行外面包裹了一个 'tr' bgcolor='#D6D3CE' 时间地点 ......
        # 如果使用 lxml 作为解析器, 会自动纠正错误
        # tr4 = trs[4]
        # special_kv = tuple(tr4.stripped_strings)[:2]
        # trs.remove(tr4)

        value_list = parse_tr_strs(trs)
        assert len(value_list) == 7

        # 前三行, 注意 value_list 第三行是有两个单元格为 None,
        # Python3 的 map 返回的是生成器, 不会立即产生结果
        # map(lambda seq: class_info.update(dict(zip(seq[0], seq[1]))), zip(key_list, value_list))
        class_info = {k: v for k, v in zip(flatten_list(key_list), flatten_list(value_list))}
        # 后四行
        class_info.update(value_list[3:])
        # class_info.update((special_kv,))
        return APIResult(response, class_info)


class SearchLessons(APIRequestBuilder):
    user_type = GUEST

    method = POST
    url = 'student/asp/xqkb1.asp'

    def __init__(self, xqdm, kcdm=None, kcmc=None):
        """
        课程查询
        :param xqdm: 学期代码
        :param kcdm: 课程代码
        :param kcmc: 课程名称
        """
        # todo:完成课程查询, 使用 kcmc 无法查询成功, 可能是请求编码有问题
        if kcdm is None and kcmc is None:
            raise ValueError('kcdm 和 kcdm 参数必须至少存在一个')
        self.data = {'xqdm': xqdm,
                     'kcdm': kcdm.upper() if kcdm else None,
                     'kcmc': kcmc}

    def after_response(self, response, *args, **kwargs):

        page = response.text
        ss = SoupStrainer('table', width='650')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)
        title = bs.find('tr', bgcolor='#FB9E04')
        trs = bs.find_all('tr', bgcolor=re.compile(r'#D6D3CE|#B4B9B9'))

        if title and trs:
            lessons = []
            keys = tuple(title.stripped_strings)
            value_list = [tr.stripped_strings for tr in trs]
            for values in value_list:
                lesson = dict(zip(keys, values))
                lesson['课程代码'] = lesson['课程代码'].upper()
                lessons.append(lesson)
            return APIResult(response, lessons)
        else:
            logger.warning('没有找到结果\n %s', self.data)
            return APIResult(response)


class GetTeachingPlan(APIRequestBuilder):
    user_type = GUEST

    method = POST
    url = 'student/asp/xqkb2.asp'

    def __init__(self, xqdm, kclxdm, ccjbyxzy):
        """
        计划查询
        :param xqdm: 学期代码
        :param kclxdm: 课程类型代码 必修为 1, 任选为 3
        :param ccjbyxzy: 专业
        """
        self.data = {'xqdm': xqdm,
                     'kclxdm': kclxdm,
                     'ccjbyxzy': ccjbyxzy}

    def after_response(self, response, *args, **kwargs):
        page = response.text
        ss = SoupStrainer('table', width='650')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)
        trs = bs.find_all('tr')
        keys = tuple(trs[1].stripped_strings)
        value_list = [tr.stripped_strings for tr in trs[2:]]
        teaching_plan = []
        for values in value_list:
            plan = dict(zip(keys, values))
            plan['课程代码'] = plan['课程代码'].upper()
            teaching_plan.append(plan)
        return APIResult(response, teaching_plan)


class GetTeacherInfo(APIRequestBuilder):
    user_type = GUEST

    method = GET
    url = 'teacher/asp/teacher_info.asp'

    def __init__(self, jsh):
        """
        查询教师信息
        :param jsh:8位教师号
        """
        self.params = {'jsh': jsh}

    def after_response(self, response, *args, **kwargs):
        page = response.text
        ss = SoupStrainer('table')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)

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
        return APIResult(response, teacher_info)


class GetLessonClasses(APIRequestBuilder):
    user_type = GUEST

    method = GET
    # url = 'student/asp/select_topRight.asp'
    url = 'student/asp/select_topRight_f3.asp'

    def __init__(self, kcdm):
        """
        获取选课系统中课程的可选教学班级
        :param kcdm:课程代码
        """
        self.params = {'kcdm': kcdm.upper()}

    def after_response(self, response, *args, **kwargs):
        page = response.text
        ss = SoupStrainer('body')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)
        class_table = bs.select_one('#JXBTable')
        if class_table.get_text(strip=True) == '对不起！该课程没有可被选的教学班。':
            return APIResult(response, None)

        result = dict()
        _, result['课程代码'], result['课程名称'] = bs.select_one('#KcdmTable').stripped_strings
        result['课程代码'] = result['课程代码'].upper()
        trs = class_table.find_all('tr')

        lesson_classes = []
        for tr in trs:
            tds = tr.find_all('td')
            assert len(tds) == 5

            # 解析隐含在 alt 属性中的信息
            class_info_table = BeautifulSoup(tds[1]['alt'], HTML_PARSER)
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

            lesson_classes.append(cls_info)

        result['可选班级'] = lesson_classes
        return APIResult(response, result)


class GetCode(APIRequestBuilder):
    user_type = STUDENT

    method = GET
    url = 'student/asp/xqjh.asp'

    def after_response(self, response, *args, **kwargs):
        page = response.text

        ss = SoupStrainer('select')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)
        xqdm_options = bs.find('select', attrs={'name': 'xqdm'}).find_all('option')
        xqdm = [{'key': node['value'], 'name': node.string.strip()} for node in xqdm_options]
        ccjbyxzy_options = bs.find('select', attrs={'name': 'ccjbyxzy'}).find_all('option')
        ccjbyxzy = [{'key': node['value'], 'name': node.string.strip()} for node in ccjbyxzy_options]
        result = {'xqdm': xqdm, 'ccjbyxzy': ccjbyxzy}

        return APIResult(response, result)


class GetStuInfo(APIRequestBuilder):
    user_type = STUDENT

    method = GET
    url = 'student/asp/xsxxxxx.asp'

    def after_response(self, response, *args, **kwargs):
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
            kv_tuple = (v.strip() for v in cell.split(':'))
            kvs.append(kv_tuple)
        stu_info.update(kvs)

        # 解析后面对应的信息
        for line in zip(key_lines, value_lines[2:]):
            stu_info.update(zip(line[0], line[1]))

        # 添加照片项
        photo_url = six.moves.urllib.parse.urljoin(response.url, bs.select_one('td[rowspan=6] img')['src'])
        stu_info['照片'] = photo_url

        return APIResult(response, stu_info)


class GetStuGrades(APIRequestBuilder):
    user_type = STUDENT

    method = GET
    url = 'student/asp/Select_Success.asp'

    def after_response(self, response, *args, **kwargs):
        page = response.text
        ss = SoupStrainer('table', width='582')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)
        trs = bs.find_all('tr')
        keys = tuple(trs[0].stripped_strings)
        # 不包括表头行和表底学分统计行
        values_list = parse_tr_strs(trs[1:-1])
        grades = []
        for values in values_list:
            grade = dict(zip(keys, values))
            grade['课程代码'] = grade['课程代码'].upper()
            grades.append(grade)
        return APIResult(response, grades)


class GetStuTimetable(APIRequestBuilder):
    user_type = STUDENT

    method = GET
    url = 'student/asp/grkb1.asp'

    def after_response(self, response, *args, **kwargs):
        page = response.text
        ss = SoupStrainer('table', width='840')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)
        trs = bs.find_all('tr')
        origin_list = parse_tr_strs(trs[1:])

        def parse_lesson(lesson):
            # todo:课程时间还有特殊情况, 例如形势政策, 应完善正则
            # 解析课程单元格
            if lesson is None:
                return None

            p = re.compile(r'(.+?)\[(.+?) \((\d{1,2})-(\d{1,2})(单|)周\)\]/')
            matched_results = p.findall(six.text_type(lesson))
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
        #
        for i in range(width):
            newline = []
            for j in range(length):
                newline.append(parse_lesson(origin_list[j][i]))
            new_matrix.append(newline)

        # 去除第一行的序号
        timetable = new_matrix[1:]
        return APIResult(response, timetable)


class GetStuFeeds(APIRequestBuilder):
    user_type = STUDENT

    method = GET
    url = 'student/asp/Xfsf_Count.asp'

    def after_response(self, response, *args, **kwargs):
        page = response.text
        ss = SoupStrainer('table', bgcolor='#000000')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)

        keys = tuple(bs.table.thead.tr.stripped_strings)
        value_trs = bs.find_all('tr', bgcolor='#D6D3CE')
        value_list = [tr.stripped_strings for tr in value_trs]
        feeds = []
        for values in value_list:
            feed = dict(zip(keys, values))
            feed['课程代码'] = feed['课程代码'].upper()
            feeds.append(feed)
        return APIResult(response, feeds)


class ChangePassword(APIRequestBuilder):
    user_type = STUDENT

    method = POST
    url = 'student/asp/amend_password_jg.asp'

    def __init__(self, oldpwd, newpwd, new2pwd):
        self.oldpwd = oldpwd
        self.newpwd = newpwd
        self.new2pwd = new2pwd
        self.data = {'oldpwd': oldpwd,
                     'newpwd': newpwd,
                     'new2pwd': new2pwd}

    def after_response(self, response, *args, **kwargs):
        page = response.text
        ss = SoupStrainer('table', width='580', border='0', cellspacing='1', bgcolor='#000000')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)
        res = bs.text.strip()
        if res == '密码修改成功！':
            return APIResult(response, True)
        else:
            logger.warning('密码修改失败\noldpwd: %s\nnewpwd: %s\nnew2pwd: %s\ntext: %s',
                           self.oldpwd, self.newpwd, self.new2pwd, res)
            return APIResult(response, False)


class SetTelephone(APIRequestBuilder):
    user_type = STUDENT

    method = POST
    url = 'student/asp/amend_tel.asp'

    def __init__(self, tel):
        """
        更新电话
        :param tel: 电话号码
        """
        self.tel = six.text_type(tel)
        self.data = {'tel': tel}

    def after_response(self, response, *args, **kwargs):
        page = response.text
        ss = SoupStrainer('input', attrs={'name': 'tel'})
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)
        return APIResult(response, bs.input['value'] == self.tel)


class GetOptionalLessons(APIRequestBuilder):
    user_type = STUDENT

    method = GET
    # url = 'student/asp/select_topLeft.asp'
    url = 'student/asp/select_topLeft_f3.asp'
    allow_redirects = False

    def __init__(self, kclx='x'):
        """
        获取可选课程, 并不判断是否选满
        :param kclx: 课程类型参数,只有三个值,{x:全校公选课, b:全校必修课, jh:本专业计划},默认为'x'
        """
        if kclx not in ('x', 'b', 'jh'):
            raise ValueError('kclx 参数不正确!')
        self.params = {'kclx': kclx}

    def after_response(self, response, *args, **kwargs):
        page = response.text
        ss = SoupStrainer('table', id='KCTable')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)
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
        return APIResult(response, lessons)


class GetSelectedLessons(APIRequestBuilder):
    user_type = STUDENT

    method = GET
    url = 'student/asp/select_down_f3.asp'

    allow_redirects = False

    def after_response(self, response, *args, **kwargs):
        page = response.text
        ss = SoupStrainer('table', id='TableXKJG')
        bs = BeautifulSoup(page, HTML_PARSER, parse_only=ss)

        lessons = []
        keys = tuple(bs.find('tr', bgcolor='#296DBD').stripped_strings)
        value_list = [tr.stripped_strings for tr in bs.find_all('tr', bgcolor='#D6D3CE')]
        for values in value_list:
            lesson = dict(zip(keys, values))
            lesson['课程代码'] = lesson['课程代码'].upper()
            lessons.append(lesson)
        return APIResult(response, lessons)


class ChangeLesson(APIRequestBuilder):
    user_type = STUDENT

    method = POST
    url = 'student/asp/selectKC_submit_f3.asp'

    allow_redirects = False

    def __init__(self, xh, kcdm, jxbh):
        self.data = {'xh': xh, 'kcdm': kcdm, 'jxbh': jxbh}

    def after_response(self, response, *args, **kwargs):
        if response.status_code == 302:
            msg = '提交选课失败, 可能是身份验证过期或选课系统已关闭'
            logger.error(msg)
            raise ValueError(msg)
        else:
            page = response.text
            # 当选择同意课程的多个教学班时, 若已选中某个教学班, 再选择其他班数据库会出错,
            # 其他一些不可预料的原因也会导致数据库出错
            p = re.compile(r'(成功提交选课数据|容量已满,请选择其他教学班|已成功删除下列选课数据).+?'
                           r'课程代码：\s*([\dbBxX]+)[\s;&nbsp]*教学班号：\s*(\d{4})', re.DOTALL)
            r = p.findall(page)
            if not r:
                logger.warning('正则没有匹配到结果, 可能出现了一些状况')
                return APIResult(response)
            results = []
            for g in r:
                logger.info(' '.join(g))
                result = dict(msg=g[0], kcdm=g[1], jxbh=g[2])
                results.append(result)
            return APIResult(response, results)
