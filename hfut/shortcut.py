# -*- coding:utf-8 -*-
from __future__ import unicode_literals, division

import json
import time
from copy import deepcopy
from multiprocessing.dummy import Pool

from .interface import GetSystemStatus, GetClassStudents, GetClassInfo, SearchCourse, GetTeachingPlan, \
    GetTeacherInfo, GetCourseClasses, GetEntireCurriculum, GetCode, GetMyInfo, GetMyAchievements, GetMyCurriculum, \
    GetMyFees, ChangePassword, SetTelephone, GetOptionalCourses, GetSelectedCourses, ChangeCourse, \
    GetUnfinishedEvaluation, EvaluateCourse
from .log import logger
from .session import GuestSession, StudentSession
from .value import HF

__all__ = ['BaseShortcuts', 'Guest', 'Student']


class BaseShortcuts(object):
    session = NotImplemented

    def query(self, interface):
        kwargs = deepcopy(interface.request_kwargs)
        kwargs.update(interface.send_kwargs)
        kwargs.update(interface.extra_kwargs)
        response = self.session.request(**kwargs)
        return interface.parse(response)


class Guest(BaseShortcuts):
    def __init__(self, *args, **kwargs):
        self.session = GuestSession(*args, **kwargs)

    def get_system_status(self):
        """
        获取教务系统当前状态信息, 包括当前学期以及选课计划

        @structure {'当前学期': str, '选课计划': [(float, float)], '当前轮数': int or None}
        """
        return self.query(GetSystemStatus())

    def get_class_students(self, xqdm, kcdm, jxbh):
        """
        教学班查询, 查询指定教学班的所有学生

        @structure {'学期': str, '班级名称': str, '学生': [{'姓名': str, '学号': int}]}

        :param xqdm: 学期代码
        :param kcdm: 课程代码
        :param jxbh: 教学班号
        """
        return self.query(GetClassStudents(xqdm, kcdm, jxbh))

    def get_class_info(self, xqdm, kcdm, jxbh):
        """
        获取教学班详情, 包括上课时间地点, 考查方式, 老师, 选中人数, 课程容量等等信息

        @structure {'校区': str,'开课单位': str,'考核类型': str,'课程类型': str,'课程名称': str,'教学班号': str,'起止周': str,
        '时间地点': str,'学分': float,'性别限制': str,'优选范围': str,'禁选范围': str,'选中人数': int,'备注': str}

        :param xqdm: 学期代码
        :param kcdm: 课程代码
        :param jxbh: 教学班号
        """
        return self.query(GetClassInfo(xqdm, kcdm, jxbh))

    def search_course(self, xqdm, kcdm=None, kcmc=None):
        """
        课程查询

        @structure [{'任课教师': str, '课程名称': str, '教学班号': str, '课程代码': str, '班级容量': int}]

        :param xqdm: 学期代码
        :param kcdm: 课程代码
        :param kcmc: 课程名称
        """
        return self.query(SearchCourse(xqdm, kcdm, kcmc))

    def get_teaching_plan(self, xqdm, kclx='b', zydm=''):
        """
        专业教学计划查询, 可以查询全校公选课, 此时可以不填 `zydm`

        @structure [{'开课单位': str, '学时': int, '课程名称': str, '课程代码': str, '学分': float}]

        :param xqdm: 学期代码
        :param kclx: 课程类型参数,只有两个值 b:专业必修课, x:全校公选课
        :param zydm: 专业代码, 可以从 :meth:`models.StudentSession.get_code` 获得
        """
        return self.query(GetTeachingPlan(xqdm, kclx, zydm))

    def get_teacher_info(self, jsh):
        """
        教师信息查询

        @structure {'教研室': str, '教学课程': str, '学历': str, '教龄': str, '教师寄语': str, '简 历': str, '照片': str,
         '科研方向': str, '出生': str, '姓名': str, '联系电话': [str], '职称': str, '电子邮件': str, '性别': str, '学位': str,
          '院系': str]

        :param jsh: 8位教师号, 例如 '05000162'
        """
        return self.query(GetTeacherInfo(jsh))

    def get_course_classes(self, kcdm):
        """
        获取选课系统中课程的可选教学班级(不可选的班级即使人数未满也不能选)

        @structure {'可选班级': [{'起止周': str, '考核类型': str, '教学班附加信息': str, '课程容量': int, '选中人数': int,
         '教学班号': str, '禁选专业': str, '教师': [str], '校区': str, '优选范围': [str], '开课时间,开课地点': [str]}],
        '课程代码': str, '课程名称': str}

        :param kcdm: 课程代码
        """
        return self.query(GetCourseClasses(kcdm))

    def get_entire_curriculum(self, xqdm=None):
        """
        获取全校的学期课程表, 当没有提供学期代码时默认返回本学期课程表

        @structure {'课表': [[[{'上课周数': [int], '课程名称': str, '课程地点': str}]]], '起始周': int, '结束周': int}

        :param xqdm: 学期代码
        """
        return self.query(GetEntireCurriculum(xqdm))


class Student(Guest):
    def __init__(self, *args, **kwargs):
        self.session = StudentSession(*args, **kwargs)

    def get_code(self):
        """
        获取当前所有的学期, 学期以及对应的学期代码, 注意如果你只是需要获取某个学期的代码的话请使用 :func:`util.cal_term_code`

        @structure {'专业': [{'专业代码': str, '专业名称': str}], '学期': [{'学期代码': str, '学期名称': str}]}

        """
        return self.query(GetCode())

    def get_my_info(self):
        """
        获取个人信息

        @structure {'婚姻状况': str, '毕业高中': str, '专业简称': str, '家庭地址': str, '能否选课': str, '政治面貌': str,
         '性别': str, '学院简称': str, '外语语种': str, '入学方式': str, '照片': str, '联系电话': str, '姓名': str,
         '入学时间': str, '籍贯': str, '民族': str, '学号': int, '家庭电话': str, '生源地': str, '出生日期': str,
         '学籍状态': str, '身份证号': str, '考生号': int, '班级简称': str, '注册状态': str}
        """
        return self.query(GetMyInfo())

    def get_my_achievements(self):
        """
        获取个人成绩

        @structure [{'教学班号': str, '课程名称': str, '学期': str, '补考成绩': str, '课程代码': str, '学分': float, '成绩': str}]
        """
        return self.query(GetMyAchievements())

    def get_my_curriculum(self):
        """
        获取个人课表

        @structure {'课表': [[[{'上课周数': [int], '课程名称': str, '课程地点': str}]]], '起始周': int, '结束周': int}
        """
        return self.query(GetMyCurriculum())

    def get_my_fees(self):
        """
        收费查询

        @structure [{'教学班号': str, '课程名称': str, '学期': str, '收费(元): float', '课程代码': str, '学分': float}]
        """
        return self.query(GetMyFees())

    def change_password(self, new_password):
        """
        修改教务密码, **注意** 合肥校区使用信息中心账号登录, 与教务密码不一致, 即使修改了也没有作用, 因此合肥校区帐号调用此接口会直接报错

        @structure bool

        :param new_password: 新密码
        """

        if self.session.campus == HF:
            raise ValueError('合肥校区使用信息中心账号登录, 修改教务密码没有作用')
        # 若新密码与原密码相同, 直接返回 True
        if new_password == self.session.password:
            raise ValueError('原密码与新密码相同')

        result = self.query(ChangePassword(self.session.password, new_password))
        if result:
            self.session.password = new_password
        return result

    def set_telephone(self, tel):
        """
        更新电话

        @structure bool

        :param tel: 电话号码, 需要满足手机和普通电话的格式, 例如 `18112345678` 或者 '0791-1234567'
        """
        return self.query(SetTelephone(tel))

    # ========== 选课功能相关 ==========
    def get_optional_courses(self, kclx='x'):
        """
        获取可选课程, 并不判断是否选满

        @structure [{'学分': float, '开课院系': str, '课程代码': str, '课程名称': str, '课程类型': str}]

        :param kclx: 课程类型参数,只有三个值,{x:全校公选课, b:全校必修课, jh:本专业计划},默认为'x'
        """
        return self.query(GetOptionalCourses(kclx))

    def get_selected_courses(self):
        """
        获取所有已选的课程

        @structure [{'费用': float, '教学班号': str, '课程名称': str, '课程代码': str, '学分': float, '课程类型': str}]
        """
        return self.query(GetSelectedCourses())

    def get_unfinished_evaluation(self):
        """
        获取未完成的课程评价

        @structure [{'教学班号': str, '课程名称': str, '课程代码': str}]
        """
        return self.query(GetUnfinishedEvaluation())

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
        return self.query(EvaluateCourse(
            kcdm, jxbh,
            r101, r102, r103, r104, r105, r106, r107, r108, r109,
            r201, r202, advice
        ))

    def change_course(self, select_courses=None, delete_courses=None):
        """
        修改个人的课程

        @structure [{'费用': float, '教学班号': str, '课程名称': str, '课程代码': str, '学分': float, '课程类型': str}]

        :param select_courses: 形如 ``[{'kcdm': '9900039X', 'jxbhs': {'0001', '0002'}}]`` 的课程代码与教学班号列表,
          jxbhs 可以为空代表选择所有可选班级
        :param delete_courses: 需要删除的课程代码集合, 如 ``{'0200011B'}``
        :return: 选课结果, 返回选中的课程教学班列表, 结构与 ``get_selected_courses`` 一致
        """
        # 框架重构后调整接口的调用
        t = self.get_system_status()
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
            logger.warning(msg)

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
            if not teaching_classes:
                logger.warning('课程[%s]没有可选班级', kcdm)
                continue

            # 反正是统一提交, 不需要判断是否已满
            optional_jxbhs = {c['教学班号'] for c in teaching_classes['可选班级']}
            if jxbhs:
                wrong_jxbhs = jxbhs.difference(optional_jxbhs)
                if wrong_jxbhs:
                    msg = '课程[{}]{}没有教学班号{}'.format(kcdm, teaching_classes['课程名称'], wrong_jxbhs)
                    logger.warning(msg)
                jxbhs = jxbhs.intersection(optional_jxbhs)
            else:
                jxbhs = optional_jxbhs

            for jxbh in jxbhs:
                kcdms_data.append(kcdm)
                jxbhs_data.append(jxbh)

        return self.query(ChangeCourse(self.session.account, select_courses, delete_courses))

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
        t = self.get_system_status()
        if not (t['选课计划'][0][1] < now < t['选课计划'][2][1]):
            logger.warning('只推荐在第一轮选课结束到第三轮选课结束之间的时间段使用本接口!')

        def iter_kcdms():
            for l in self.get_optional_courses():
                yield l['课程代码']

        kcdms = kcdms or iter_kcdms()

        def target(kcdm):
            course_classes = self.get_course_classes(kcdm)
            if course_classes:
                course_classes['可选班级'] = [c for c in course_classes['可选班级'] if c['课程容量'] > c['选中人数']]
                if len(course_classes['可选班级']) > 0:
                    # http://stackoverflow.com/questions/6319207/are-lists-thread-safe
                    return course_classes

        # Python 2.7 不支持 with 语法
        pool = Pool(5)
        result = list(filter(None, pool.map(target, kcdms)))
        pool.close()
        pool.join()

        if dump_result:
            json_str = json.dumps(result, ensure_ascii=False, indent=4, sort_keys=True)
            with open(filename, 'wb') as fp:
                fp.write(json_str.encode(encoding))
            logger.info('可选课程结果导出到了:%s', filename)
        return result
