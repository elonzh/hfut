# -*- coding:utf-8 -*-
# qpy:webapp
# qpy://127.0.0.1:8080
"""
使用 bottle 编写的一个简单课表查看页面, 可以筛选每周的课程, 可以在手机上安装 qpython 并安装好依赖后在手机上运行
"""
from bottle import Bottle, template

import hfut

index_tpl = """
<!DOCTYPE html>
<html lang="cn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="initial-scale=1.0">
    <title>第{{week}}周课表</title>
    <style>
        table{margin: 0 auto;border-collapse:collapse;}
        table, th, td{border: 1px solid;}
        thead{background-color: #EFC363;}
        tbody{background-color: #D6D3CE;}
        caption{margin-bottom:0.5em;}
        .index-td{text-align:center}
    </style>
</head>
<body onload="document.getElementById('opt_' + '{{week}}').selected = true">
<table>
    <caption>
        <select id="week" onchange="window.location=document.getElementById('week').value">
            %for i in range(start, end+1):
                <option id="opt_{{i}}" value="{{i}}">
                    第{{i}}周
                </option>
            %end
        </select>
    </caption>
    <thead>
        <tr>
            <th></th>
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
                <td class="index-td">{{i+1}}</td>
                %for j in range(7):
                    %if curriculum[j][i]:
                        <td>
                            %for c in curriculum[j][i]:
                                {{c[u'课程名称']}}:{{c[u'课程地点']}}/
                            %end
                        </td>
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
session = hfut.Student('你的学号', '密码', '校区')
curriculum = session.get_my_curriculum()
start = curriculum[u'起始周']
end = curriculum[u'结束周']
filtered = [None] * (end - start + 1)


@app.route('/')
@app.route('/<week:int>')
def index(week=1):
    idx = week - 1
    filtered[idx] = filtered[idx] or hfut.util.filter_curriculum(curriculum[u'课表'], week)
    return template(index_tpl, curriculum=filtered[idx], week=week, start=start, end=end)


if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
