.. _quickstart:

快速上手
============

迫不及待了吗？本页内容为如何入门 hfut_stu_lib 提供了很好的指引.其假设你已经安装了 hfut_stu_lib.如果还没有，
去 :ref:`安装 <install>` 一节看看吧.

首先，确认一下:

* hfut_stu_lib 已 :ref:`安装 <install>`
* hfut_stu_lib 已 :ref:`更新 <updates>`


.. _commonparm:
通用参数说明
--------------------

参数与教务的网络请求参数基本一致

- ``xqdm``: 学期代码， 形如 '027'， '027' 的字符串
- ``kcdm``: 课程代码， 形如 '1400011B' 的字符串
- ``zydm``: 专业代码， 形如 '0120123111' 的字符串
- ``jxbh``: 教学班号， 形如 '0001' 的字符串
- ``kcmc``: 课程名称关键字
- ``jsh`` : 教师号， 形如 '12000198' 的字符串
- ``kclx``: 课程类型， 有 'x'(选修)， 'b'(必修)， 'jh'(本专业计划)三个选项


调用接口
----------

    >>> from hfut_stu_lib import StudentSession
    >>> stu = StudentSession('your-account', 'your-password')
    >>> stu.get_my_info()

所有的接口在这哦 :ref:`所有接口 <api>`.

不会玩儿? 快瞧瞧 :ref:`高级技巧 <advanced>` 这一节.
