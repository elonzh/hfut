- 20150903 v0.0.2
    . 重构了 StuLib.select_lesson 的参数处理过程, 由于第二次选课结束暂时没有完成对提交结果的处理
    . 添加 Travis IC 持续集成工具
    
- 20150902 v0.0.1
    . 修复 StuLib.get_class_info 出错
    . 添加 教师信息查询（StuLib.get_teacher_info） 功能
    . 将 StuLib.get_url 的 code 修改为对应的方法名称
    . 修复 StuLib.change_password 正则匹配不完整的问题
    . 修复 StuLib.set_telephone 正则匹配不完整的问题
    . 添加部分单元测试
    . 调整了包的结构