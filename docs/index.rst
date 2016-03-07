hfut_stu_lib - 合工大教务接口文档
===========================================

版本 v\ |version|. (:ref:`安装 <install>`)

开发状态
-----------

.. include:: dev-state.rst

hfut_stu_lib provided full-featured interfaces for the educational administration system of HeFei University of Technology.

hfut_stu_lib 提供了合肥工业大学教务系统学生端接口并提供了方便开发者开发围绕学生数据的一些工具.

.. warning:: 由于本部的登录方式有所不同,本部教务系统暂时无法使用,需要本部同学提供登陆方式进行测试.

功能特性
--------

- 使用简单, 只需声明一个  :class:`~hfut_stu_lib.StudentSession`  对象即可调用所有接口
- 接口丰富, 提供了所有学生能够使用的教务接口, 除此外还有众多正常情况下学生无法访问到的接口
- 支持会话自动更新, 你无需担心超过时间后访问接口会出错
- 提供了强大的选课接口, 你能轻松查询可选的课程, 查看教学班级选中人数, 批量提交增删课程数据
- 数据能够轻松导出, 能够为基于工大教务数据的服务或应用提供强大的底层支持
- 对开发友好, 提供了用于继承的基类以及页面处理的函数和其他工具提升你的开发效率
- Python2/3 兼容, 代码在 2.7,3.3,3.4,3.5 四个版本上进行了测试


它能做什么？
---------------

- 学生微信后台服务支持
- 选课助手
- 学生数据分析
- OAuth 登陆服务
- 以及一切你能想到的与学生信息与教务数据有关的项目, 例如这个根据学生地址信息定位并统计全国学生分布的示例应用, 顺带了快速找老乡功能, 当然由于时间原因它还未完成 `locate_my_fellow <https://github.com/er1iang/locate_my_fellow>`_.


用户指南
-----------

这部分文档主要介绍了 hfut_stu_lib 的背景,然后对于 hfut_stu_lib 的应用做了一步一步的要点介绍.

.. toctree::
    :maxdepth: 1

    user/intro
    user/install
    user/quickstart
    user/advanced


API 指南
-----------

在这里你能看到所有接口的文档.

.. toctree::
    :maxdepth: 3

    autodoc/hfut_stu_lib

社区指南
----------

这部分文档主要详细地介绍了 hfut_stu_lib 的社区支持情况.

.. toctree::
    :maxdepth: 1

    community/faq
    community/recommended
    community/support
    community/updates

索引
------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
