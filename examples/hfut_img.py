# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import six
import threading
import logging
import requests
import os
import sys
from hfut_stu_lib import GuestSession

# 文件保存路径
DIR_NAME = 'img'
# 起始年份
START_YEAR = 2012
# 结束年份
END_YEAR = 2015

# 宣城校区
HOST = 'http://222.195.8.201/student/photo/'
# 本部地址
# HOST = 'http://121.251.19.29/student/photo/'
# 所有人都上的课程
LESSON_CODE = '1400011B'  # 高等数学(A）

# 设置日志
logger = logging.Logger('hfut_img', level=logging.WARNING)
sh = logging.StreamHandler()
fh = logging.FileHandler('hfut_img.log', encoding='utf-8')
fmt = logging.Formatter('%(threadName)s %(levelname)s %(lineno)s行: - %(asctime)s\n\t %(message)s', '%d日 %H:%M')
sh.setFormatter(fmt)
fh.setFormatter(fmt)
logger.addHandler(sh)
logger.addHandler(fh)
logger.setLevel(logging.INFO)

# 初始化 session
session = GuestSession()


def year2term_code(year):
    return ''.join(['0', six.text_type(int(year) - 1991)])


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
    klass = session.search_course(term_code, LESSON_CODE)
    if klass:
        logger.info('{} 学期共有 {} 个教学班'.format(term_code, len(klass)))
        for k in klass:
            # 获取教学班学生
            class_stus = session.get_class_students(term_code, LESSON_CODE, k['教学班号'])
            if class_stus is None:
                logger.critical('没有获取到 {} 学期的教学班'.format(term_code))
                sys.exit(0)
            stu_num = len(class_stus['学生'])
            logger.info('{} 班共有 {} 名学生'.format(class_stus['班级名称'], stu_num))
            stu_sum += stu_num
            for stu in class_stus['学生']:
                img_url = six.moves.urllib.parse.urljoin(HOST, ''.join([stu['学号'][:4], '/', stu['学号'], file_suffix]))
                sex = '男'
                stu_name = stu['姓名']
                if stu['姓名'].endswith('*'):
                    sex = '女'
                    stu_name = stu_name[:-1]
                full_name = ''.join([stu['学号'], '-', sex, '-', stu_name])
                filename = os.path.join(DIR_NAME, stu['学号'][:4], ''.join([full_name, file_suffix]))
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
        term_code = year2term_code(year)
        t = threading.Thread(target=fetch_img, name=year, args=(term_code,))
        t.start()
