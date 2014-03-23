# coding: utf8
""" 管理平台, 主要负责添加商品
"""

from util.base import BaseHandler


def url_spec(**kwargs):
    return [
        (r'/manager/?', ManagerHandler, kwargs),
    ]


class ManagerHandler(BaseHandler):
    """ 添加商品
    """

    def get(self):
        return self.render('manager.html')

    def post(self):
        pass