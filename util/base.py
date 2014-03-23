# coding: utf8
# 基础request封装, 约定:
# 记录用户: 安全cookie保存用户id, key(token), cache保存用户对象(使用cpickle.dumps序列化对象), 每次更新用户信息需要及时更新缓存
# 登录: 在config中设置登录url, 需要登录才能访问的接口需要添加login_required()修饰器即可, 默认web模式


from tornado.web import RequestHandler, MissingArgumentError, HTTPError
import json

import cache
from config import configs


class RequestData(dict):
    """  请求数据对象
    """
    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            return None

    def __setattr__(self, key, value):
        self[key] = value

    def validate(self, required=None):
        """ 请求数据验证方法
        """
        if required:
            for key in required:
                if not self[key]:
                    raise HTTPError(400, '[Bad Request]: request data illegal',  reason='Bad-Request')
        return True


##基础封装RequestHandler
class BaseHandler(RequestHandler):

    def form_data(self):
        """ web 端 获取表单全部数据 - 字典
        """
        data = {}
        for k in self.request.arguments:
            v = self.get_arguments(k)
            data[k] = v[0] if len(v) == 1 else v
        return RequestData(data)

    def get_args(self, key, default='', data_type=unicode):
        """ 获取post或者get数据的某个参数
        """
        try:
            data = self.get_argument(key)
            if callable(data_type):
                return data_type(data)
            return data
        except MissingArgumentError:
            return default

    def get_template_namespace(self):
        """ 添加额外的模板变量, 默认有:
         handler=self,
         request=self.request,
         current_user=self.current_user,
         locale=self.locale,
          _=self.locale.translate,
         static_url=self.static_url,
         xsrf_form_html=self.xsrf_form_html,
         reverse_url=self.reverse_url
        """
        add_names = dict(
            get_flashed_message=self.get_flashed_message,
        )
        name = super(BaseHandler, self).get_template_namespace()
        name.update(add_names)
        return name

    def flash(self, msg):
        """ 消息闪现
        """
        self.clear_cookie('message')
        self.set_cookie('message', msg)

    def get_flashed_message(self):
        msgs = self.get_cookie('message', '')
        self.clear_cookie('message')
        return msgs

    @property
    def ip(self):
        return self.request.headers.get('X-Real-Ip', self.request.remote_ip)

    def write(self, chunk):
        if isinstance(chunk, dict) and self.settings.get('debug'):
            RequestHandler.write(self, json.dumps(chunk, indent=4))
        else:
            RequestHandler.write(self, chunk)
        if isinstance(chunk, dict):
            self.set_header('Content-Type', self._ct('json'))

    def write_error(self, status_code, **kwargs):
        """ 异常状态码处理
        """
        if 'exc_info' in kwargs:  # 设置错误码
            code = -1
            try:
                error = kwargs['exc_info'][1].log_message
                code = configs['error_codes'].get(error, -1)
                self.set_header('error-msg', unicode(error))
            except (KeyError, AttributeError):
                pass
            self.set_header('error', code)
        return super(BaseHandler, self).write_error(status_code, **kwargs)

    def get_error_html(self, error_code, **kwargs):
        pass