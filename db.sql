-- create database hqerp default character set utf8mb4;

use shopping;
-- 商品基本信息表
drop table if exists `item`;
create table `item` (
  id INTEGER NOT NULL AUTO_INCREMENT,
  title VARCHAR(128) comment '名称',
  `desc` text comment '描述',
  category_id int(11) comment '分类id',
  category varchar(32) comment '分类名称',
  mall varchar(128) comment '来源地址',
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP comment '创建时间',
  primary key(id)
) engine=MyISAM;


-- 价格表
DROP TABLE IF EXISTS price;
CREATE TABLE price (
    id INTEGER NOT NULL AUTO_INCREMENT,
    item_id int(11),
    size VARCHAR(64) comment '尺寸',
    color varchar(64) comment '颜色',
    brand varchar(64) comment '品牌',
    weight varchar(32) comment '重量',
    price decimal(10,2) comment '价格',
    discount varchar(32) comment '折扣',
    org_price decimal(10,2) comment '原始价格',
    cur_price decimal(10,2) comment '当前价格',
    internal decimal(10,2) comment '成本价',
    `status` int(11) default 0 comment '库存量',
    images varchar(512) comment '商品图片',
    shipping_fee decimal(10,2) comment '运送费用',
    created TIMESTAMP default CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) engine=MyISAM;


-- 历史价格
drop table if exists history_price;
create table history_price (
  id INTEGER NOT NULL AUTO_INCREMENT,
  price_id int(11),
  item_id int(11),
  price decimal(10,2),
  `time` TIMESTAMP,
  primary key(id)
) engine=MyISAM;


-- 类别表
DROP TABLE IF EXISTS category;
CREATE TABLE category (
    id INTEGER NOT NULL AUTO_INCREMENT,
    title varchar(64),
    `count` int(11) default 0,
    PRIMARY KEY (id)
) engine=MyISAM;