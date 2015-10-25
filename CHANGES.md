- 20151025 v0.2.0
    1. 调整了模块结构
    2. 分离了 session 与 接口, 通过一个统一的 AuthSession 自动绑定接口, 参数原来 StuLib 接口参数相同
    3. 区分了用户类型, AuthSession 即使没有登录也能访问公共接口了
    4. 添加了 regist_api , 现在你可以在不修改模块代码的情况下添加自己的接口了

- 20150912 v0.1.3
    1. 修复因 StuLib 初始化时未对 stu_id 进行类型转换而导致 StuLib.get_stu_info 出错的问题
    
- 20150912 v0.1.2
    1. 修复安装时 README.md 缺失的问题
  
- 20150912 v0.1.1
    1. 添加了一些单元测试
    
- 20150911 v0.1.0
    1. 解决 requests 不能对 GBK 转 UTF8 无损转换的问题
    2. 添加 StuLib.catch_response , 抽象了响应的获取, 提升了代码的可维护性

- 20150910 v0.0.4
    1. 修复了 StuLib.get_class_student 中由于教务网页代码严重的错误导致页面无法解析而不可用的问题
    2. 添加了 StuLib.get_class_student 的测试用例
    3. 由于 requests 返回的的网页无法做到无损转码, 将传递 BeautifulSoup 的文档改为原始编码文档,将转码工作交给 BeautifulSoup 处理, 但用到正则匹配的方法还存在此问题

- 20150909 v0.0.3
    1. 统一将返回的课程代码进行大写转换, 避免因学校课程代码大小写的不统一产生不可预料的问题
    2. 重构了 StuLib.select_lesson , 现在支持更好地批量选课以及更好地结果处理过程
    3. 重构了 StuLib.delete_lesson , 现在支持批量删课以及更好地结果处理过程

- 20150903 v0.0.2
    1. 重构了 StuLib.select_lesson 的参数处理过程, 由于第二次选课结束暂时没有完成对提交结果的处理
    2. 添加 Travis IC 持续集成工具

- 20150902 v0.0.1
    1. 修复 StuLib.get_class_info 出错
    2. 添加 教师信息查询（StuLib.get_teacher_info） 功能
    3. 将 StuLib.get_url 的 code 修改为对应的方法名称
    4. 修复 StuLib.change_password 正则匹配不完整的问题
    5. 修复 StuLib.set_telephone 正则匹配不完整的问题
    6. 添加部分单元测试
    7. 调整了包的结构