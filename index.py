# coding: utf8
""" 首页, 商品展示
"""

from util.base import BaseHandler


def url_spec(**kwargs):
    return [
        (r'/(index)?/?', IndexHandler, kwargs),
    ]


class IndexHandler(BaseHandler):

    def get(self):
        self.write('Shopping Demo')


