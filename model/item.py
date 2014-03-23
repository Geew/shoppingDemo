# coding: utf8

from util.simpleOrm import HqOrm
from config import configs


class Item(HqOrm):
    """ 商品基本信息
    """

    _table_name = 'item'
    _rows = (
        'id', 'title', 'desc', 'category_id', 'category', 'mall', 'created',
    )
    _db_config = configs['db_config']

    @property
    def prices(self):
        """ 商品各种类型的价格综合对象
        """
        return Price.find(item_id=self.id)


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