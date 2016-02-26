hfut_stu_lib - 合肥工业大学教务接口文档
===========================================

版本 v\ |version|. (:ref:`安装 <install>`)


hfut_stu_lib provided full-featured interfaces for the educational administration system of HeFei University of Technology.

hfut_stu_lib 提供了合肥工业大学教务系统学生端接口并提供了方便开发者开发围绕学生数据的一些工具。

.. warning:: 由于本部的登录方式有所不同，本部教务系统暂时无法使用，需要本部同学提供登陆方式进行测试。

功能特性
--------

- 动态绑定接口， 只需声明一个  :class:`~hfut_stu_lib.AuthSession`  对象即可调用不同用户类型接口
- 对开发友好， 你可以使用编写自己的接口而不需要修改代码， 模块会自动注册


它能做什么？
---------------

- 学生微信后台服务支持
- 选课助手
- 学生数据分析
- OAuth 登陆服务
- 以及一切你能想到的与学生信息与教务数据有关的项目， 例如这个根据学生地址信息定位并统计全国学生分布的示例应用， 顺带了快速找老乡功能， 当然由于时间原因它还未完成 `locate_my_fellow <https://github.com/er1iang/locate_my_fellow>`_。


用户指南
-----------

这部分文档主要介绍了 hfut_stu_lib 的背景，然后对于 hfut_stu_lib 的应用做了一步一步的要点介绍。

.. toctree::
    :maxdepth: 1

   user/intro
   user/install
   user/quickstart
   user/advanced


社区指南
----------

这部分文档主要详细地介绍了 hfut_stu_lib 的社区支持情况。

.. toctree::
    :maxdepth: 1

    community/faq
    community/recommended
    community/support
    community/updates


API 索引
-----------

在这里你能看到所有接口的文档。

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`