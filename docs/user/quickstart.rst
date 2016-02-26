.. _quickstart:

快速上手
============

迫不及待了吗？本页内容为如何入门 hfut_stu_lib 提供了很好的指引。其假设你已经安装了 hfut_stu_lib。如果还没有，
去 :ref:`安装 <install>` 一节看看吧。

首先，确认一下：

* hfut_stu_lib is :ref:`installed <install>`
* hfut_stu_lib is :ref:`up-to-date <updates>`


.. _commonparm:
通用参数说明
--------------------

参数与教务的网络请求参数基本一致

- ``auth_session``: :class:`AuthSession <hfut_stu_lib.AuthSession>`
- ``xqdm``: 学期代码， 形如 '027'， '027' 的字符串
- ``kcdm``: 课程代码， 形如 '1400011B' 的字符串
- ``jxbh``: 教学班号， 形如 '0001' 的字符串
- ``kcmc``: 课程名称关键字
- ``jsh`` : 教师号， 形如 '12000198' 的字符串
- ``kclx``: 课程类型， 有 'x'(选修)， 'b'(必修)， 'jh'(本专业计划)三个选项


调用接口
----------

    >>> from hfut_stu_lib import AuthSession, STUDENT
    >>> stu = AuthSession('your-account', 'your-password', STUDENT)
    >>> stu.get_stu_info()

通过简单的声明对象后， 你就可以使用各个接口了， 如果你使用的是公共接口， 则不需要任何参数，
这种调用方式是不需要填写 ``auth_session`` 参数的， 因为注册为方法后默认将你使用的 :class:`~hfut_stu_lib.AuthSession` 对象带入，
当然你也可以这么做(实际使用强烈不推荐)::

    >>> from hfut_stu_lib import AuthSession, STUDENT
    >>> from hfut_stu_lib.api import get_stu_info
    >>> stu = AuthSession('your-account', 'your-password', STUDENT)
    >>> get_stu_info(stu)

需要更多知识？ 请阅读 :ref:`高级技巧 <advanced>` 这一节。
