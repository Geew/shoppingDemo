# coding: utf8
#!/usr/bin/env python

import os.path
import sys
sys.path.append(os.path.dirname(__file__))

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from config import configs


class Application(tornado.web.Application):
    def __init__(self):
        handlers = []
        handler_mods = [
            'manager',
        ]
        for i in handler_mods:
            m = __import__('handler.' + i, fromlist=['url_spec'])
            handlers.extend(m.url_spec())
        handler_mods = [
            'index',
        ]
        for i in handler_mods:
            m = __import__(i, fromlist=['url_spec'])
            handlers.extend(m.url_spec())

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), 'templates'),
            static_path=os.path.join(os.path.dirname(__file__), 'static'),
            cookie_secret=configs['cookie_secret'],
            autoescape=None,  # disable escaping
            debug=configs['debug'],
            gzip=True,
            #xsrf_cookies=True,  # csrf enabled
        )
        tornado.web.Application.__init__(self, handlers, **settings)


def main():
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(configs['port'])
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()