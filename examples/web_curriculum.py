# -*- coding:utf-8 -*-
# qpy:2
# qpy:webapp
# qpy://127.0.0.1:8080
"""
使用 bottle 编写的一个简单课表查看页面, 可以筛选每周的课程, 可以在手机上安装 qpython 并安装好 hfu_stu_lib 后在手机上运行
"""
from bottle import Bottle, template
from hfut_stu_lib import StudentSession
from hfut_stu_lib.util import filter_curriculum

index_tpl = """
<!DOCTYPE html>
<html lang="cn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>第{{week}}周课表</title>
</head>
<body onload="document.getElementById('opt_' + '{{week}}').selected = true">
<table border=1px>
    <thead>
    <tr>
        <th>
            <select id="week" onchange="window.location=document.getElementById('week').value">
                %for i in range(start, end+1):
                    <option id="opt_{{i}}" value="{{i}}">
                        第{{i}}周
                    </option>
                %end
            </select>
        </th>
        <th>周一</th>
        <th>周二</th>
        <th>周三</th>
        <th>周四</th>
        <th>周五</th>
        <th>周六</th>
        <th>周日</th>
    </tr>
    </thead>
    <tbody>
        %for i in range(11):
            <tr>
                <td style="text-align:center">{{i+1}}</td>
                %for j in range(7):
                    %if curriculum[j][i]:
                        <td>{{curriculum[j][i][0][u'课程名称']}}:{{curriculum[j][i][0][u'课程地点']}}</td>
                    %else:
                        <td></td>
                    %end
                %end
            </tr>
        %end
    </tbody>
</table>
</body>
</html>
"""
app = Bottle()
stu = StudentSession(2013217413, 'pyth0n')
c = stu.get_my_curriculum()
start = c[u'起始周']
end = c[u'结束周']
filtered = [None] * (end - start + 1)


@app.route('/')
@app.route('/<week:int>')
def index(week=1):
    idx = week - 1
    if filtered[idx] is None:
        filtered[idx] = filter_curriculum(c['课表'], week)
    return template(index_tpl, curriculum=filtered[idx], week=week, start=start, end=end)


if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
