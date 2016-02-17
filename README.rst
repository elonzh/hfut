############
hfut-stu-lib
############

.. image:: https://badge.fury.io/py/hfut_stu_lib.svg
:target: http://badge.fury.io/py/hfut_stu_lib

.. image:: https://travis-ci.org/er1iang/hfut-stu-lib.svg?branch#dev
:target: https://travis-ci.org/er1iang/hfut-stu-lib

.. image:: https://landscape.io/github/er1iang/hfut-stu-lib/dev/landscape.svg?style#flat
:target: https://landscape.io/github/er1iang/hfut-stu-lib/dev

.. image:: https://coveralls.io/repos/er1iang/hfut-stu-lib/badge.svg?branch#dev&service#github
:target: https://coveralls.io/github/er1iang/hfut-stu-lib?branch#dev

-----

Provided full-featured interfaces for the educational administration system of HeFei University of Technology.

提供了合肥工业大学教务系统学生端接口并提供了方便开发者开发围绕学生数据的一些工具

由于本部的登录方式有所不同, 本部教务系统暂时无法使用

欢迎编程爱好者star或者fork, 同时为想学 Python 的新手提供一些指导

.. contents:: 目录

-----

########
主要特性
########

* 动态绑定接口, 只需声明一个 AuthSession 对象即可调用不同用户类型接口
* 内置了缓存管理工具, 同样也只要声明一个缓存管理对象, 就能使用全局地管理缓存
* 对开发友好, 你可以使用编写自己的接口而不需要修改代码, 模块会自动注册, 当然缓存功能也是

############
它能做什么？
############

* 学生微信后台服务支持
* 选课助手
* 学生数据分析
* OAuth 登陆服务
* 以及一切你能想到的与学生信息与教务数据有关的项目, 例如这个根据学生地址信息定位并统计全国学生分布的示例应用, 顺带了快速找老乡功能233333, 当然由于时间原因它还未完成 `locate_my_fellow <https://github.com/evilerliang/locate_my_fellow>`_

####
安装
####

你可以直接使用提交到 PyPi 版本::

    $ pip install hfut_stu_lib

由于学校网络原因你可能无法下载成功, 你可以把 pip 的仓库设置为国内镜像, 当然你也可以选择这里的 master 分支下载稳定的版本, 切换到解压后的目录, 运行::

    $ python setup.py install

来安装

####
使用
####

* 调用接口::

    >>> from hfut_stu_lib import AuthSession, STUDENT
    >>> stu = AuthSession('your-account', 'your-password', STUDENT)
    >>> stu.get_stu_info()

通过简单的声明对象后, 你就可以使用各个接口了, 如果你使用的是公共接口, 则不需要任何参数, 这种调用方式是不需要填写 session 参数的, 因为注册为方法后默认将你使用的 AuthSession 对象带入, 当然你也可以这么做(实际使用强烈不推荐)::

    >>> from hfut_stu_lib import AuthSession, STUDENT
    >>> from hfut_stu_lib import get_stu_info
    >>> stu = AuthSession('your-account', 'your-password', STUDENT)
    >>> get_stu_info(stu)


############
已支持的接口
############

* 公用接口
    #. `get_class_students(auth_session, xqdm, kcdm, jxbh)`: 获取指定教学班的学生
    #. `get_class_info(auth_session, xqdm, kcdm, jxbh)`: 查询班级信息
    #. `search_lessons(auth_session, xqdm, kcdm=None, kcmc=None)`: 搜索课程
    #. `get_teaching_plan(auth_session, xqdm, kclxdm, ccjbyxzy)`: 获取教学计划
    #. `get_teacher_infoget_teacher_info(auth_session, jsh)`: 查询教师信息
    #. `get_lesson_classes(auth_session, kcdm, detail=False)`: 查询课程可选班级
* 学生接口
    #. `get_code(auth_session)`: 获取所有的专业代码和学期代码
    #. `get_stu_info(auth_session)`: 查询个人信息
    #. `get_stu_grades(auth_session)`: 查询个人成绩
    #. `get_stu_timetable(auth_session, detail=False)`: 查询个人课表
    #. `get_stu_feeds(auth_session)`: 查询个人收费
    #. `change_password(auth_session, oldpwd, newpwd, new2pwd)`: 修改密码
    #. `set_telephone(auth_session, tel)`: 设置电话
    #. `get_optional_lessons(auth_session, kclx='x')`: 查询可选课程
    #. `get_selected_lessons(auth_session)`: 获取已选课程
    #. `is_lesson_selected(auth_session, kcdm)`: 检查课程是否已选
    #. `select_lesson(auth_session, kvs)`: 批量选择课程, 可以自动选择可用班级
    #. `delete_lesson(auth_session, kcdms)`: 批量删除课程

* 通用参数说明
    参数与教务的网络请求参数基本一致

    * `xqdm`: 学期代码, 形如 '027', '027' 的字符串
    * `kcdm`: 课程代码, 形如 '1400011B' 的字符串
    * `jxbh`: 教学班号, 形如 '0001' 的字符串
    * `kcmc`: 课程名称关键字
    * `jsh`: 教师号, 形如 '12000198' 的字符串
    * `kclx`: 课程类型, 有 'x'(选修), 'b'(必修), 'jh'(本专业计划)三个选项


* 开发及拓展模块
    你可以开发自己额外的接口和缓存管理对象, 只要注意一下规则即可, 或者 fork 一个分支, 开发好了提交 PullRequest 合并到这个项目中

**更新日志请查看：** `CHANGES.md <https://github.com/evilerliang/hfut-stu-lib/blob/master/CHANGES.md>`_
