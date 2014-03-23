#!/usr/bin/env python
# coding: utf-8
"""
基础ORM功能, 使用方式如下:

    # 定义
    class TestModel(HqOrm):
        _table_name = 'test_mode'
        _rows = ['id', 'name', 'created', 'status']

        _status_ok = 1
        _status_del = 0

        @classmethod
        def find_fix_name(cls, name):
            return cls.find(name=name, status=cls._status_ok)  # find 类方法
            # get: cls.get(id=234)
            # page: cls.page(name__like='hello', page=2, order_by='created desc')
            # number: cls.number(**kwargs)
            # etc ....

        @property
        def status_label(self):
            return {self._status_ok: u'正确', self._status_del: u'已删除'}

    # 使用
    # new
    tm = TestModel.new(name='hello', status=TestModel._status_ok, created=datetime.now())
    # get
    test_mode = TestModel.get(id=23)
    test_mode.dictify(fields=['name'], properties=['status_label'])
    test_mode.name = 'new name'
    test_mode.save()
    # 更多方法看源码吧
"""

from torndb import Connection
import logging
import datetime
import time


_CONNS_ = {}


def get_conn(host, database, user=None, password=None, pre_exe=None):
    """ 数据库连接
        pre_exe: 数据库准备执行语句, 列表方式罗列
    """
    key = ''.join((host, database, str(user), str(password)))
    if key in _CONNS_:
        return _CONNS_[key]
    _CONNS_[key] = con = Connection(host=host, database=database, user=user, password=password)
    con._db_args.pop('init_command', None)
    con.execute("SET TIME_ZONE = 'SYSTEM'")
    if pre_exe:
        for sql in pre_exe:
            try:
                con.execute(sql)
            except:
                pass
    return con


# 定义异常
class BuildArgsError(Exception):
    """ 参数重构错误
    """
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class SqlValueError(Exception):
    pass


# 比较运算 exam: age__gt = 34 //age 大于34
_COMS = {'gt': '>',  # 大于
         'lt': '<',  # 小于
         'ge': '>=',  # 大于等于
         'le': '<=',  # 小于等于
         'no': '<>',  # 不等于
         'like': ' like ', }


def _rebuild_argv(kwargs, args=None, rows=None, link=' and ', table=None):
    """ 重构字典参数,以及连接成sql语句需要的字符串
        args: (re_str, values)
        kwargs: key, value dict
        return where expr
    """
    keys = kwargs.keys()
    check_keys = [k.split('__')[0] for k in keys]
    # 检测更新列是否都在表列中
    if rows and not set(check_keys).issubset(set(rows)):
        raise BuildArgsError(
            ''.join((str(check_keys), '<>', str(rows)))
        )
    _keys_str = []
    _values = []
    _list_args = []
    for k, v in kwargs.items():
        com = '='
        sk = '`' + k + '`'
        if table:
            sk = table + '.' + sk
        if isinstance(v, (list, tuple)):
            # 构建or语句
            if len(v) > 1:
                _tk = (sk+'=%s', ) * len(v)
                _list_args.append(('('+' or '.join(_tk)+')', v))
                continue
            if not v:
                raise SqlValueError
            v = v[0]
        if '__' in k:
            k1, k2 = k.split('__')
            if k2 == 'like':
                v = ''.join(('%', v, '%'))
            com = _COMS.get(k2, '=')
            if com != '=':
                sk = sk.replace(k, k1)
        _values.append(v)
        _keys_str.append(''.join((sk, com, '%s')))
    if args:
        _list_args.append(args)
    for item in _list_args:
        _keys_str.append(item[0])
        _values.extend(item[1])
    _keys_str = link.join(_keys_str)
    _keys_str = ' (' + _keys_str + ') ' if kwargs else _keys_str
    return _keys_str, _values


def and_(args=None, **kwargs):
    """
        args: (keys_str, values)
        kwargs: key=value
        return: (keys_str, values) tuple
    """
    return _rebuild_argv(kwargs, link=' and ', args=args)


def or_(args=None, **kwargs):
    return _rebuild_argv(kwargs, link=' or ', args=args)


def where_(args=None, **kwargs):
    return _rebuild_argv(kwargs, link=' and ', args=args)


def set_(**kwargs):
    return _rebuild_argv(kwargs, link=' , ')


def list_to_sql(l, table=''):
    """ 列表列转换sql语句返回, 如果是字符串形式的sql, 直接返回
    """
    if isinstance(l, (str, unicode)):
        return l
    if table:
        table += '.'
    return ','.join([table+'`'+str(i)+'`' for i in l])


def join_(table, on_str, **kwargs):
    """
        join_(table='items', on_str='items.id=topic_item.item_id', status=1)
    """
    join_str = ' JOIN `' + table + '` on ' + on_str
    re_str, values = _rebuild_argv(kwargs, table=table)
    return join_str, re_str, values


def _execute_sql(sql, values, db_con, mode='execute', echo=False):
    """ 连接到数据库执行sql语句, mode: execute/get/query
    """
    if echo:
        logging.info('[HqOrm Gen-SQL]:' + sql % tuple(values))
    return getattr(db_con, mode)(sql, *values)


class HqOrm(object):

    # 必须在子类中重置的属性
    _table_name = None  # 数据库表名
    _rows = None  # 表列名
    # 数据库链接配置
    _db_config = None
    # 是否打印sql语句
    _echo = False

    # 可选提供属性
    _per_page = 10

    # 内置属性, 外部不使用
    __dirty_data = {}

    def __init__(self, data):
        """ data must be a dict
        """
        #self._table_name = '_'.join(i.lower() for i in re.findall(r'[A-Z][a-z]+', self.__class__.__name__))
        #设置数据属性
        for k in data:
            self.__setattr__(k, data[k])
        self.__dirty_data.clear()

    def __setattr__(self, key, value):
        """ 设置属性
        """
        object.__setattr__(self, key, value)
        if key in self._rows:
            self.__dirty_data[key] = value

    def __getitem__(self, key):
        """ 中括号操作支持
        """
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError

    # 定义类级别的操作方法
    @classmethod
    def new(cls, **kwargs):
        """ 新建一条记录并保存到数据库, 返回对象
        """
        if not kwargs:
            return None

        xid = kwargs.get('id')  # 自定义id
        values = kwargs.values()

        row_names = list_to_sql(kwargs.keys())
        row_values = ','.join(['%s'] * len(values))

        # 构建sql插入语句
        sql = "INSERT INTO `" + cls._table_name + "` ( " + row_names + " ) VALUES ( " + row_values + " ) "
        max_try = 3
        for i in range(max_try):
            try:
                _db_con = get_conn(**cls._db_config)
                nid = _execute_sql(sql, values, db_con=_db_con, mode='execute', echo=cls._echo)
            except Exception as ex:
                if ex[0] == 1062:
                    continue
                else:
                    raise ex
            break
        else:
            raise Exception(cls.__name__ + ' error', ex[1])
        nid = xid or nid
        add = cls.get(id=nid)
        add.__dirty_data.clear()
        return add  # 返回对象

    @classmethod
    def new_mul(cls, *items):
        """ 新建多个记录到数据库, 返回新建对象列表, 参数items为字典列表
        sql_rows = _to_sql(str(items[0].keys())[1:-1])
        values = []
        data_len = len(items[0])
        for data in items:
            values.extend(data.values())
        row_values = ('(' + ','.join(['%s']) * data_len + ')') * len(items)
        sql = 'INSERT INTO `' + cls._table_name + '` (' + sql_rows + ') VALUES ' + row_values
        """
        news = []
        if not items:
            return []
        for data in items:
            news.append(cls.new(**data))
        return news

    @classmethod
    def __get(cls, tn, fields, **kwargs):
        """ sql 缓存中间层
        """
        is_o = not fields
        fields = fields or cls._rows
        re_str, values = _rebuild_argv(kwargs, rows=cls._rows)
        _where = ''.join((' WHERE ', re_str)) if re_str else ''
        sql = ''.join(
            ('SELECT ', list_to_sql(fields), ' FROM ',  '`', tn, '`', _where, ' LIMIT 1')
        )
        return sql, values, is_o

    @classmethod
    def get(cls, fields=None, **kwargs):
        """ 获取单个对象, 根据id获取, 取得多个对象将导致异常
        """
        sql, values, is_o = cls.__get(tn=cls._table_name, fields=fields, **kwargs)
        _db_con = get_conn(**cls._db_config)
        o = _execute_sql(sql, values, db_con=_db_con, mode="get", echo=cls._echo)
        if is_o and o:
            return cls(o)
        return o

    @classmethod
    def __find(cls, tn, args, join, fields, order_by, limit, **kwargs):
        is_o = not fields
        fields = fields or cls._rows
        if order_by:
            order_by = ' ORDER BY ' + order_by
        if limit != '':  # 避免limit=0的bug
            limit = ' LIMIT ' + str(limit)
        table = cls._table_name if join else ''
        re_str, values = _rebuild_argv(kwargs, args=args, rows=cls._rows, table=table)
        join_sql = ''
        if join:
            if re_str and join[1]:
                re_str += ' AND '
            re_str = ''.join((re_str, join[1]))
            values.extend(join[2])
            join_sql = join[0]
        _where = ''.join((' WHERE ', re_str)) if re_str else ''
        sql = ''.join(
            ('SELECT ', list_to_sql(fields, table=table), ' FROM `', tn, '` ', join_sql, _where
             , order_by, limit)
        )
        return sql, values, is_o

    @classmethod
    def find(cls, args=None, join=None, fields=None, order_by='', limit='', **kwargs):
        """ 根据条件获取多个对象, 返回对象列表, 支持单张连表
            exam: find(id=id, name=name) -- and
        """
        sql, values, is_o = cls.__find(tn=cls._table_name, args=args, join=join, fields=fields,
                                       order_by=order_by, limit=limit, **kwargs)
        _db_con = get_conn(**cls._db_config)
        ds = _execute_sql(sql, values, db_con=_db_con, mode='query', echo=cls._echo)
        return [cls(o) for o in ds] if is_o else ds

    @classmethod
    def find_iter(cls, args=None, join=None, fields=None, order_by='', limit='', **kwargs):
        """ 数据迭代器
        """
        sql, values, is_o = cls.__find(tn=cls._table_name, args=args, join=join, fields=fields,
                                       order_by=order_by, limit=limit, **kwargs)
        _db_con = get_conn(**cls._db_config)
        return _execute_sql(sql, values, db_con=_db_con, mode='iter', echo=cls._echo)

    @classmethod
    def all(cls, fields=None, order_by='', limit=''):
        is_o = not fields
        fields = fields or cls._rows
        if order_by:
            order_by = ' ORDER BY ' + order_by
        if limit != '':
            limit = ' LIMIT ' + str(limit)
        sql = ''.join(
            ('select ', list_to_sql(fields), ' from ', cls._table_name, order_by, limit)
        )
        _db_con = get_conn(**cls._db_config)
        ds = _execute_sql(sql, [], db_con=_db_con, mode='query', echo=cls._echo)
        return [cls(d) for d in ds] if is_o else ds

    @classmethod
    def __page(cls, tn, page, args, join, fields, order_by, per_page, **kwargs):
        is_o = not fields
        fields = fields or cls._rows

        page = int(page)
        page = max(page-1, 0)
        beg = page * per_page
        if order_by:
            order_by = ' ORDER BY ' + order_by
        #table = join and cls._table_name or ''
        table = cls._table_name if join else ''
        re_str, values = _rebuild_argv(kwargs, args=args, rows=cls._rows, table=table)
        join_sql = ''
        if join:
            if re_str and join[1]:
                re_str += ' AND '
            re_str = re_str + join[1]
            values.extend(join[2])
            join_sql = join[0]
        _where = ''.join((' WHERE ', re_str)) if re_str else ''
        page_limit = ' LIMIT %s OFFSET %s' % (per_page, beg)
        sql = ''.join(
            ('SELECT ', list_to_sql(fields, table=table), ' FROM `', tn, '` ', join_sql, _where,
             order_by, page_limit)
        )
        return sql, values, is_o

    @classmethod
    def page(cls, page, args=None, join=None, fields=None, order_by='', per_page=None, **kwargs):
        """ 页数从第1页开始, 支持单张连表
            page: 页数
            args: and, or支持
            join: join exp [table, join_col, table.col]
            fields: 连表获取的列字符串 exam: 'items.*'
            kwargs: 限制条件
        """
        per_page = per_page or cls._per_page
        sql, values, is_o = cls.__page(tn=cls._table_name, page=page, args=args, join=join,
                                       fields=fields, order_by=order_by, per_page=per_page, **kwargs)
        _db_con = get_conn(**cls._db_config)
        ds = _execute_sql(sql, values, db_con=_db_con, mode='query', echo=cls._echo)
        return [cls(o) for o in ds] if is_o else ds

    @classmethod
    def __delete(cls, tn, args, **kwargs):
        re_str, values = _rebuild_argv(kwargs, args=args, rows=cls._rows)
        sql = ''.join(
            ('DELETE FROM `', tn, '` WHERE ', re_str)
        )
        return sql, values

    @classmethod
    def delete(cls, args=None, **kwargs):
        """ 删除相关对象, 直接生效, 谨慎操作
        """
        sql, values = cls.__delete(tn=cls._table_name, args=args, **kwargs)
        _db_con = get_conn(**cls._db_config)
        return _execute_sql(sql, values, db_con=_db_con, mode='execute_rowcount', echo=cls._echo)

    @classmethod
    def __number(cls, tn, args, **kwargs):
        re_str, values = _rebuild_argv(kwargs, args=args, rows=cls._rows)
        #sql = 'SELECT COUNT(*) FROM `%s` WHERE %s' % (cls._table_name, re_str)
        _where = ''.join((' WHERE ', re_str)) if re_str else ''
        sql = ''.join(
            ('SELECT COUNT(*) FROM `', tn, '` ', _where)
        )
        return sql, values

    @classmethod
    def number(cls, args=None, **kwargs):
        """ 计数
        """
        sql, values = cls.__number(tn=cls._table_name, args=args, **kwargs)
        _db_con = get_conn(**cls._db_config)
        result = _execute_sql(sql, values, db_con=_db_con, mode='query', echo=cls._echo)
        return int(result[0].get('COUNT(*)', 0)) if result else 0

    @classmethod
    def __cls_update(cls, tn, sets, args, **kwargs):
        set_keys, set_values = sets
        set_keys = set_keys.replace('(', '').replace(')', '')
        re_str, values = _rebuild_argv(kwargs, args=args, rows=cls._rows)
        #sql = 'UPDATE `%s` SET %s WHERE %s' % (cls._table_name, set_keys, re_str)
        _where = ''.join((' WHERE ', re_str)) if re_str else ''
        sql = ''.join(
            ('UPDATE `', tn, '` SET ', set_keys, _where)
        )
        set_values.extend(values)
        return sql, set_values

    @classmethod
    def cls_update(cls, sets=None, args=None, **kwargs):
        """
            类级别的更新方法
            usage: Cls.cls_update(set_(a=32, b=34), and_(id=3, status=0))
        """
        if not sets:
            return 0
        sql, set_values = cls.__cls_update(tn=cls._table_name, sets=sets, args=args, **kwargs)
        _db_con = get_conn(**cls._db_config)
        return _execute_sql(sql, set_values, db_con=_db_con, mode='execute_rowcount', echo=cls._echo)

    def __update(self, tn, **kwargs):  # 必须带上至少一个差异性参数 kwargs 带有self.id
        re_str, values = _rebuild_argv(kwargs, args=None, rows=self._rows, link=' , ')
        re_str = re_str.replace('(', '').replace(')', '')  # update 语句不可包含括号
        #sql = '%s` SET %s WHERE `id` = "%s"' % (self._table_name, re_str, self.id)
        sql = ''.join(
            ('UPDATE `', tn, '` SET ', re_str, ' WHERE `id` = "', str(self.id), '"')
        )
        return sql, values

    # 对象级别方法
    def update(self, **kwargs):
        """ 更新对象多个值, 单个值直接设置并调用save方法即可
        """
        if not kwargs:
            return self
        kwargs['id'] = self.id
        sql, values = self.__update(tn=self._table_name, **kwargs)
        _db_con = get_conn(**self._db_config)
        rows = _execute_sql(sql, values, db_con=_db_con, mode='execute_rowcount', echo=self._echo)
        if rows:
            # 更新成功, 设置新的属性
            for k in kwargs:
                self.__setattr__(k, kwargs[k])
            self.__dirty_data.clear()
        return self

    def save(self):
        """ 保存更改到数据库
        """
        self.update(**self.__dirty_data)
        self.__dirty_data.clear()
        return self

    def be_clean(self):
        self.__dirty_data.clear()

    def dictify(self, fields=None, properties=None, convert_date=True):
        """ 对象数据包装, 返回字典
        """
        if properties is None:
            properties = []
        data = {}
        for k, v in self.__dict__.items():
            if fields and k in fields:
                data[k] = v
            elif not k.startswith('_') and fields is None:
                data[k] = v
        for attr in properties:
            if hasattr(self, attr) and attr not in data:
                data[attr] = getattr(self, attr)
        # 设置时间字段为时间戳
        if convert_date:
            for k in data:
                v = data[k]
                if isinstance(v, (datetime.datetime, datetime.date)):
                    data[k] = int(time.mktime(v.timetuple()))
        return data