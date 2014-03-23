# coding: utf-8
""" 配置模块
"""

from tornado import options

APP_RUN_PORT = 8885
APP_DB_NAME = 'shopping'
APP_REDIS_NAME = 'shopping'

configs = {
    'debug': True,
    'db_name': APP_DB_NAME,
    'redis_name': APP_REDIS_NAME,
    'db_config': {'host': 'localhost', 'database': APP_DB_NAME, 'user': 'root', 'pre_exe': ('set names utf8', )},
    'redis': {
        APP_REDIS_NAME: {'host': 'localhost', 'port': 6379},
    }
}


options.define('port', default=APP_RUN_PORT, help='server listening port', type=int)
options.define('conf', default=None, help='configuration file', type=str)