# -*- coding:utf-8 -*-
"""
日志模块
"""
from __future__ import unicode_literals

from logging import Logger, WARNING, StreamHandler, Formatter

__all__ = ['logger', 'report_response', 'log_result_not_found']

logger = Logger('hfut', level=WARNING)

sh = StreamHandler()
# https://docs.python.org/3/library/logging.html#logrecord-attributes
fmt = Formatter('[%(levelname)s]%(module)s.%(funcName)s at %(lineno)d: %(message)s')
sh.setFormatter(fmt)
logger.addHandler(sh)


def report_response(response,
                    request_headers=True, request_body=True,
                    response_headers=False, response_body=False,
                    redirection=False):
    """
    生成响应报告

    :param response: ``requests.models.Response`` 对象
    :param request_headers: 是否加入请求头
    :param request_body: 是否加入请求体
    :param response_headers: 是否加入响应头
    :param response_body: 是否加入响应体
    :param redirection: 是否加入重定向响应
    :return: str
    """
    # https://docs.python.org/3/library/string.html#formatstrings
    url = 'Url: [{method}]{url} {status} {elapsed:.2f}ms'.format(
        method=response.request.method, url=response.url,
        status=response.status_code, elapsed=response.elapsed.total_seconds() * 1000
    )
    pieces = [url]

    if request_headers:
        request_headers = 'Request headers: {request_headers}'.format(request_headers=response.request.headers)
        pieces.append(request_headers)
    if request_body:
        request_body = 'Request body: {request_body}'.format(request_body=response.request.body)
        pieces.append(request_body)
    if response_headers:
        response_headers = 'Response headers: {response_headers}'.format(response_headers=response.headers)
        pieces.append(response_headers)
    if response_body:
        response_body = 'Response body: {response_body}'.format(response_body=response.text)

    reporter = '\n'.join(pieces)

    if redirection and response.history:
        for h in response.history[::-1]:
            redirect_reporter = report_response(
                h,
                request_headers, request_body,
                response_headers, response_body,
                redirection=False
            )
            reporter = '\n'.join([redirect_reporter, ' Redirect ↓ '.center(72, '-'), reporter])

    return reporter


def log_result_not_found(response):
    msg = '\n'.join([
        '没有解析到结果, 可能是参数不正确, 服务器出错, 解析有问题, 如果本库有问题请及时进行反馈.',
        report_response(response, response_headers=True, response_body=True, redirection=True)
    ])
    logger.warning(msg)
