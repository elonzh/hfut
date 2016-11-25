# -*- coding:utf-8 -*-
"""
抓取全校学生的照片
"""
from __future__ import unicode_literals

import logging
import os
import sys
import threading

import requests
import six

from hfut import Guest, XC, HF
from hfut.util import cal_term_code

# 文件保存路径
DIR_NAME = 'img'
# 起始年份
START_YEAR = 2012
# 结束年份
END_YEAR = 2015

# 校区
campus = XC

# 所有人都上的课程 # 军事训练
if campus == HF:
    COURSE_CODE = '52000020'
else:
    COURSE_CODE = '5200023B'

# 设置日志
logger = logging.Logger('hfut_img', level=logging.WARNING)
sh = logging.StreamHandler()
fh = logging.FileHandler('hfut_img.log', encoding='utf-8')
fmt = logging.Formatter('%(threadName)s %(levelname)s %(lineno)s行: - %(asctime)s\n\t %(message)s', '%d %H:%M')
sh.setFormatter(fmt)
fh.setFormatter(fmt)
logger.addHandler(sh)
logger.addHandler(fh)
logger.setLevel(logging.INFO)

# 初始化 session
shortcuts = Guest(campus)


# 初始化文件夹
def setup_dir():
    if not os.path.isdir(DIR_NAME):
        os.mkdir(DIR_NAME)
        logger.info('成功创建目录 {}'.format(DIR_NAME))
    for i in range(START_YEAR, END_YEAR + 1):
        path = os.path.join(DIR_NAME, six.text_type(i))
        if not os.path.isdir(path):
            os.mkdir(path)
            logger.info('成功创建目录 {}'.format(path))


# 下载照片
def fetch_img(term_code):
    file_suffix = '.jpg'
    stu_sum = 0
    success_sum = 0
    fail_sum = 0
    error_sum = 0
    exist_sum = 0
    # 获取该学期的所有教学班
    klass = shortcuts.search_course(term_code, COURSE_CODE)
    if klass:
        logger.info('{} 学期共有 {} 个教学班'.format(term_code, len(klass)))
        for k in klass:
            # 获取教学班学生
            class_stus = shortcuts.get_class_students(term_code, COURSE_CODE, k['教学班号'])
            if class_stus is None:
                logger.critical('没有获取到 {} 学期的教学班'.format(term_code))
                sys.exit(0)
            stu_num = len(class_stus['学生'])
            logger.info('{} 班共有 {} 名学生'.format(class_stus['班级名称'], stu_num))
            stu_sum += stu_num
            for stu in class_stus['学生']:
                year = str(stu['学号'] // 1000000)
                code = str(stu['学号'])
                img_url = six.moves.urllib.parse.urljoin(shortcuts.session.host, ''.join(
                    ['student/photo/', year, '/', code, file_suffix]))
                sex = '男'
                stu_name = stu['姓名']
                if stu['姓名'].endswith('*'):
                    sex = '女'
                    stu_name = stu_name[:-1]
                full_name = ''.join([code, '-', sex, '-', stu_name])
                filename = os.path.join(DIR_NAME, year, ''.join([full_name, file_suffix]))
                if os.path.isfile(filename):
                    logger.warning('{} 的照片已下载过'.format(full_name))
                    exist_sum += 1
                    continue
                try:
                    res = requests.get(img_url)
                    if res.status_code == 200:
                        with open(filename, 'wb') as fp:
                            fp.write(res.content)
                        logger.info('下载 {} 的照片成功'.format(full_name))
                        success_sum += 1
                    elif res.status_code == 404:
                        logger.warning('下载 {} 的照片失败'.format(full_name))
                        fail_sum += 1
                except Exception as e:
                    logger.error('下载 {} 的照片出错\n\t{}'.format(full_name, e))
                    error_sum += 1
        logger.info('{} 学期共有 {} 名学生'.format(term_code, stu_sum))
        logger.info('{} 学期下载完成,成功 {},失败 {},错误 {}, 已存在 {}'.format(
            term_code, success_sum, fail_sum, error_sum, exist_sum))
    else:
        logger.critical('没有获取到第 {} 的教学班级'.format(term_code))
        sys.exit(0)


if __name__ == '__main__':
    setup_dir()
    for year in range(START_YEAR, END_YEAR + 1):
        term_code = cal_term_code(year)
        t = threading.Thread(target=fetch_img, name=year, args=(term_code,))
        t.start()
