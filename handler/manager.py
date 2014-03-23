# coding: utf8
""" 管理平台, 主要负责添加商品
"""

from util.base import BaseHandler
from model.item import ItemForm, PriceForm, Item, Price


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
        item_form = ItemForm(self.request.arguments)
        price_form = PriceForm(self.request.arguments)
        if item_form.validate() and price_form.validate():
            item = Item.new(**item_form.data)
            if item:
                data = dict(price_form.data)
                data['item_id'] = item.id
                Price.new(**data)
                return self.redirect('/')
            else:
                self.flash(u'创建商品失败, 请重试')
        else:
            self.flash(u'表单错误,请检查')
        return self.redirect(self.request.uri)