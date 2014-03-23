# coding: utf8
""" 首页, 商品展示
"""

from util.base import BaseHandler
from model.item import Item


def url_spec(**kwargs):
    return [
        (r'/(index)?/?', IndexHandler, kwargs),
        (r'/item/(?P<iid>\d+)/?', ItemHandler, kwargs),
    ]


class IndexHandler(BaseHandler):

    def get(self, *args):
        items = Item.explore()
        return self.render('index.html', items=items)


class ItemHandler(BaseHandler):

    def get(self, *args, **kwargs):
        pass
