############
hfut-stu-lib
############

.. image:: https://badge.fury.io/py/hfut_stu_lib.svg
    :target: http://badge.fury.io/py/hfut_stu_lib

.. image:: https://travis-ci.org/evilerliang/hfut-stu-lib.svg?branch#dev
    :target: https://travis-ci.org/evilerliang/hfut-stu-lib

.. image:: https://landscape.io/github/evilerliang/hfut-stu-lib/dev/landscape.svg?style#flat
    :target: https://landscape.io/github/evilerliang/hfut-stu-lib/dev

.. image:: https://coveralls.io/repos/evilerliang/hfut-stu-lib/badge.svg?branch#dev&service#github
    :target: https://coveralls.io/github/evilerliang/hfut-stu-lib?branch#dev

-----

Provided full-featured interfaces for the educational administration system of HeFei University of Technology.

提供了合肥工业大学教务系统学生端接口并提供了方便开发者开发围绕学生数据的一些工具
由于本部的登录方式有所不同, 本部教务系统暂时无法使用

.. contents::
    :local:
    :depth: 1
    :backlinks: none

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

############
已支持的接口
############

* 公用接口
    #. `get_class_students(session, xqdm, kcdm, jxbh)`: 获取指定教学班的学生
    #. `get_class_info(session, xqdm, kcdm, jxbh)`: 查询班级信息
    #. `search_lessons(session, xqdm, kcdm=None, kcmc=None)`: 搜索课程
    #. `get_teaching_plan(session, xqdm, kclxdm, ccjbyxzy)`: 获取教学计划
    #. `get_teacher_infoget_teacher_info(session, jsh)`: 查询教师信息
    #. `get_lesson_classes(session, kcdm, detail=False)`: 查询课程可选班级
* 学生接口
    #. `get_code(session)`: 获取所有的专业代码和学期代码
    #. `get_stu_info(session)`: 查询个人信息
    #. `get_stu_grades(session)`: 查询个人成绩
    #. `get_stu_timetable(session, detail=False)`: 查询个人课表
    #. `get_stu_feeds(session)`: 查询个人收费
    #. `change_password(session, oldpwd, newpwd, new2pwd)`: 修改密码
    #. `set_telephone(session, tel)`: 设置电话
    #. `get_optional_lessons(session, kclx='x')`: 查询可选课程
    #. `get_selected_lessons(session)`: 获取已选课程
    #. `is_lesson_selected(session, kcdm)`: 检查课程是否已选
    #. `select_lesson(session, kvs)`: 批量选择课程, 可以自动选择可用班级
    #. `delete_lesson(session, kcdms)`: 批量删除课程

* 通用参数说明
    参数与教务的网络请求参数基本一致
    * `xqdm`: 学期代码, 形如 '027', '027' 的字符串
    * `kcdm`: 课程代码, 形如 '1400011B' 的字符串
    * `jxbh`: 教学班号, 形如 '0001' 的字符串
    * `kcmc`: 课程名称关键字
    * `jsh`: 教师号, 形如 '12000198' 的字符串
    * `kclx`: 课程类型, 有 'x'(选修), 'b'(必修), 'jh'(本专业计划)三个选项


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

* 使用缓存
    默认的, 如果你没有使用缓存, 调用接口你会收到一条警告, 因为缓存很实用而且使用简单, 库中默认有 `MemoryCache` 和  `FileCache` 两种方式, 你只需要在使用前声明一个缓存管理对象就行了, 注意缓存是全局管理并使用了单例模式, 只有第一次声明有效, 多次声明你将收到警告并且不会有任何更改::

        >>> from hfut_stu_lib import AuthSession, STUDENT, MemoryCache
        >>> from hfut_stu_lib import get_stu_info
        >>> mc = MemoryCache()
        >>> stu = AuthSession('your-account', 'your-password', STUDENT)
        >>> get_stu_info(stu)

    你可以直接使用你声明的缓存管理对象管理缓存, 推荐的做法是使用 `g` 对象, 它是一个全局的变量, 它有 `registered_api`, `cached_api`, `current_cache_manager` 三个属性

    * `registered_api` : 一个字典, 包含了所有注册的接口的属性
    * `cached_api`: 一个字典, 包含了所有需要缓存结果的接口属性
    * `current_cache_manager`: 一个缓存管理对象

    由于缓存是使用接口的名称,调用参数, 是否可以共享三者字典的md5值来索引,你很可能需要使用 `cal_cache_md5` 函数来计算 md5::

        >>> from hfut_stu_lib import g
        >>> from hfut_stu_lib.util import cal_cache_md5
        >>> cache = cal_cache_md5(func, session, is_public, *args, **kwargs) # 参数分别为 接口对象, 会话对象, 是否共享, 以及其他接口调用的参数
        >>> g.current_cache_manager.get(cache)

* 开发及拓展模块
    你可以开发自己额外的接口和缓存管理对象, 只要注意一下规则即可
    一个接口大概是这样的::

        from hfut_stu_lib import register_api, cache_api

        @register_api(url='请求的相对地址', method='请求方式', user_type='用户类型')
        @cache_api(duration='缓存时间, is_public='是否共享缓存') # 注意 cache_api 必须放在register_api的下面, 如果不需要缓存这个接口可以不使用它
        def you_function(session, *args, **kwargs)
            params = {'your-params-key': 'your-params-value'}
            # catch_response 是对 requests 库的 request 方法的封装, 具体使用请阅读相应的文档
            res = session.catch_response(you_function.func_name, '其他请求参数')
            # 然后使用html解析工具解析
            ... ...

    一个缓存管理类大概是这样的形式::

        from hfut_stu_lib import BaseCache

        class YourCacheManager(BaseCache):
            # 必须从 BaseCache 继承并实现以下方法
            def get(self, cache_md5):
                # 提取缓存
                ... ...

            def set(self, cache_md5, value, duration=None):
                # 设置缓存
                ... ...

            def delete(self, cache_md5):
                # 删除指定的缓存
                ... ...

            def drop(self):
                # 清空所有缓存
                ... ...

**更新日志请查看：** `CHANGES.md <https://github.com/evilerliang/hfut-stu-lib/blob/master/CHANGES.md>`_
