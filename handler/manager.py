# coding: utf8
""" 管理平台, 主要负责添加商品
"""

from util.base import BaseHandler


def url_spec(**kwargs):
    return [
        (r'/manager/?', ManagerHandler, kwargs),
    ]


class ManagerHandler(BaseHandler):

    def get(self):
        pass

    def post(self):
        pass