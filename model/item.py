# coding: utf8

from util.simpleOrm import HqOrm, join_
from config import configs

#form
from wtforms_tornado import Form
from wtforms.fields import StringField, DecimalField
from wtforms.validators import required


class Item(HqOrm):
    """ 商品基本信息
    """

    _table_name = 'item'
    _rows = (
        'id', 'title', 'desc', 'category_id', 'category', 'mall', 'created',
    )
    _db_config = configs['db_config']
    _echo = True

    @classmethod
    def get(cls, fields=None, **kwargs):
        item = super(Item, cls).get(fields=fields, **kwargs)
        if item:
            item.prices = Price.find(item_id=item.id)
        return item

    @property
    def image(self):
        ps = Price.find(item_id=self.id, limit=1)
        return ps[0].images if ps else configs['default_image']

    @classmethod
    def explore(cls):
        """ 获取全部商品信息, 包含价格, 每个商品为一个列表
        """
        items = cls.find(
            join=join_(table='price',
                       on_str='price.item_id=item.id',),
            order_by='item.created desc',
            fields='item.*, price.*',
        )
        result = {}
        for item in items:
            if item.id in result:
                result[item.id].append(item)
            else:
                result[item.id] = [item, ]
        return result


class Category(HqOrm):
    """ 商品类别
    """

    _table_name = 'category'
    _rows = (
        'id', 'title', 'count'
    )
    _db_config = configs['db_config']


class Price(HqOrm):
    """ 商品价格
    """

    _table_name = 'price'
    _rows = (
        'id', 'item_id', 'size', 'color', 'brand', 'weight', 'price', 'discount', 'org_price',
        'cur_price', 'internal', 'status', 'status', 'images', 'shipping_fee', 'created'
    )
    _db_config = configs['db_config']


class HistoryPrice(HqOrm):
    """ 历史价格
    """

    _table_name = 'history_price'
    _rows = (
        'id', 'item_id', 'price_id', 'price', 'time',
    )
    _db_config = configs['db_config']


class PriceForm(Form):

    size = StringField()
    brand = StringField()
    color = StringField()
    weight = StringField()
    price = DecimalField()


#  商品表单
class ItemForm(Form):

    title = StringField()
    desc = StringField()
