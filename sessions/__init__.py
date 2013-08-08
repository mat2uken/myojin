# encoding: utf-8
import random
import time
import os
from os import getpid
from datetime import datetime, timedelta

import threading
from cStringIO import StringIO
from pprint import pprint

class Debug(threading.local):
    def print_(self, *args, **kws):
        for x in args:
            print >>self.buf, x,
        for k,v in kws:
            print >>self.buf, ":%s" % k ,v,
        print >> self.buf
    def pprint(self, *args, **kws):
        for x in args:
            pprint(x, self.buf)
        if kws:
            pprint(kws, self.buf)

# using beaker session
import beaker.middleware
from beaker.middleware import SessionMiddleware
import beaker.session
from beaker.session import Session, SessionObject
from beaker.crypto import hmac as HMAC, hmac_sha1 as SHA1, md5
#from beaker.session import getpid

class CustomBeakerSession(beaker.session.Session):
    def _create_id(self):
        self.id = md5(
            md5("%f%s%f%s" % (time.time(), id({}), random.random(),
                              getpid())).hexdigest(), 
        ).hexdigest()
        self.is_new = True
        self.last_accessed = None
        if self.use_cookies:
            self.cookie[self.key] = self.id
            if self._domain:
                self.cookie[self.key]['domain'] = self._domain
            if self.secure:
                self.cookie[self.key]['secure'] = True
            self.cookie[self.key]['path'] = self._path
            if self.cookie_expires is not True:
                if self.cookie_expires is False:
                    expires = datetime.fromtimestamp( 0x7FFFFFFF )
                elif isinstance(self.cookie_expires, timedelta):
##                     expires = datetime.today() + self.cookie_expires
                    expires = datetime.now() + self.cookie_expires
                    print expires
                elif isinstance(self.cookie_expires, datetime):
                    expires = self.cookie_expires
                else:
                    raise ValueError("Invalid argument for cookie_expires: %s"
                                     % repr(self.cookie_expires))
                self.cookie[self.key]['expires'] = \
                    expires.strftime("%a, %d-%b-%Y %H:%M:%S GMT" )
            self.request['cookie_out'] = self.cookie[self.key].output(header='')
            self.request['set_cookie'] = False

## class CustomConfig(Config):
##     def from_pyfile(self, filename):
##         super(CustomConfig,self).from_pyfile(filename)

# using (override) beaker_extensions.redis_
# beaker の backends はsetuptoolsのentry_pointsを見て分岐しているので、
# パッケージとしてインストールしなければそのしくみを直接使えない。
# CustomBeakerSession をつくる際に独自のNameSpaceManagerを指定する。
#
# TODO beaker_extensions.dynomite というのがdynamodb互換っぽいが、
# pypiにそんなライブラリはないので作りなおさないとダメそう
try:
    import json
except ImportError:
    import simplejson as json
from beaker_extensions.redis_ import RedisManager
class RedisJsonManager(RedisManager):
    def __getitem__(self, key):
        return json.loads(self.db_conn.get(self._format_key(key)))
    def set_value(self, key, value, expiretime=None):
        key = self._format_key(key)
        if (expiretime is None) and (type(value) is tuple):
            expiretime = value[1]
        if expiretime:
            self.db_conn.setex(key, expiretime, json.dumps(value))
        else:
            self.db_conn.set(key, json.dumps(value))

class CustomSessionObject(SessionObject):
    def _session(self):
        """Lazy initial creation of session object"""
        if self.__dict__['_sess'] is None:
            params = self.__dict__['_params']
            environ = self.__dict__['_environ']
            self.__dict__['_headers'] = req = {'cookie_out':None}
            req['cookie'] = environ.get('HTTP_COOKIE')
            if params.get('type') == 'cookie':
                assert False
                self.__dict__['_sess'] = beaker.session.CookieSession(req)
            elif params.get('type') == 'redisjson':
                self.__dict__['_sess'] = CustomBeakerSession(req,
                        namespace_class=RedisJsonManager, use_cookies=True, **params)
            else:
                self.__dict__['_sess'] = CustomBeakerSession(req, use_cookies=True, **params)
        return self.__dict__['_sess']

    def flush(self):
        self.clear()
        self._create_id()
        self.load()

    @property
    def sid(self):
        return self.id

    def cycle_key(self):
        items = self.items()
        self.clear()
        self._create_id()
        self.load()
        for k,v in items:
            if not k.startswith("_"):
                self[k] = v
        #self.save()
        #self.persist()
        #self.load()
beaker.middleware.SessionObject = CustomSessionObject



class SQLAlchemySessionMiddleware(object):
    def __init__(self, app, flask_app):
        self.app = app
        self.flask_app = flask_app
    def __call__(self, environ, start_response):
        db = getattr(self.flask_app, "db", None)
        if db and not db.session.is_active:
            db.session.remove()
        try:
            result = self.app(environ, start_response)
        except:
            try:
                if db:
                    db.session.rollback()
            except:
                pass
            raise
        return result

# customize flask
from flask import Flask, Request#, Session
from flask import Config
import flask
import re
mobile_re = re.compile('.*(ipad|iphone|android).*')
class CustomRequest(Request):
    def __init__(self, environ):
        super(CustomRequest,self).__init__(environ)
        if 'beaker.session' in environ:
            self.session = environ['beaker.session']
    @property
    def is_get(self):
        return self.method.upper() == 'GET'

    @property
    def is_post(self):
        return self.method.upper() == 'POST'

    def judge_mobile(self):
        ret = getattr(self, '_is_mobile', None)
        if ret is None:
            def _is_mobile_():
                ua = self.environ.get('HTTP_USER_AGENT', None)
                if ua is not None:
                    self.ua = ua
                    return mobile_re.match(ua.lower()) is not None
            self._is_mobile = _is_mobile_()
            ret = self._is_mobile
        return ret
    is_mobile = property(judge_mobile, None)

    def _is_find_ua(self, string):
        key = '_is_' + string
        ret = getattr(self, key, None)
        if ret is None:
            ua = self.environ.get('HTTP_USER_AGENT', None)
            self.ua = ua
            ret = False if ua is None else ua.lower().find(string) > -1
            setattr(self, key, ret)
        return ret

    @property
    def is_android(self):
        return self._is_find_ua('android')

    @property
    def is_iphone(self):
        return self._is_find_ua('iphone')

    @property
    def is_ipad(self):
        return self._is_find_ua('ipad')

COOKIE_NAME = 'C'
class CustomFlask(Flask):
    debug_out = Debug()
    request_class = CustomRequest
    registered_check_ssl_handler = None
##     before_login_handlers = ()
##     after_login_handlers = ()
    after_auth_check_handlers = ()
    
##     def before_login_handler(self):
##         def decorator(f):
##             self.before_login_handlers += (f,)
##             return f
##         return decorator

##     def after_login_handler(self):
##         def decorator(f):
##             self.after_login_handlers += (f,)
##             return f
##         return decorator

    def create_url_adapter_(self, request):
        app = self
        environ = request.environ
        server_name = (
            app.config['SERVER_NAME'] or environ.get('HTTP_HOST') or environ.get('SERVER_NAME')
            ).split(":")[0]
        return self.url_map.bind_to_environ(request.environ,
                                            server_name=server_name)

    def after_auth_check_handler(self):
        def decorator(f):
            self.after_auth_check_handlers += (f,)
            return f
        return decorator
        
    def add_url_rule(self, rule, endpoint=None, view_func=None, debug_only=False, **options):
        if endpoint:endpoint = endpoint.replace("___",".")
        if not debug_only or self.config.get("DEBUG"):
            super(CustomFlask, self).add_url_rule(rule, endpoint, view_func, **options)
            
    def after_auth_check(self, *args, **kws):
        for h in self.after_auth_check_handlers:
            h(*args, **kws)

##     def before_login(self, *args, **kws):
##         for h in self.before_login_handlers:
##             h(*args, **kws)
    
##     def after_login(self, *args, **kws):
##         for h in self.after_login_handlers:
##             h(*args, **kws)
    check_ssl_handler = ()
    def check_ssl_handler(self):
        def decorator(f):
            self.registered_check_ssl_handler = f
            return f
        return decorator
    registered_check_ssl_handler = None
    def is_ssl_request(self):
        if self.registered_check_ssl_handler:
            return self.registered_check_ssl_handler()
        return None
        
    def __init__(self, *args, **kws):
        super(CustomFlask,self).__init__(*args, **kws)
        self.preserved = False
        self.app = self
        from flask.globals import _request_ctx_stack
        _request_ctx_stack.push(self)
        self.ssl_required_endpoints = set()

        from werkzeug import LocalStack, LocalProxy
        def get_current_user():
            from myojin.auth import UserModelBase
            return UserModelBase.current_user()
        self.current_user = LocalProxy(get_current_user)
        
        @self.before_request
        def check_request():
            app = self
            if not app.config.get('SSL_REQUIRED_REDIRECT'):
                return
            from flask import request, jsonify, session
            from flask import Module, abort, redirect
            environ = request.environ
            if not app.is_ssl_request() and app.in_ssl_required_endpoint(request.endpoint):
                server_name = (
                    app.config.get('SSL_HOST', None) or app.config['SERVER_NAME'] or environ.get('HTTP_HOST') or environ.get('SERVER_NAME')
                    ).split(":")[0]

                query_string = environ.get('QUERY_STRING', '')
                query_splitter = "?" if query_string else ""
                path_info = request.environ['PATH_INFO']
                return redirect("https://%s%s%s%s" % (server_name, path_info, query_splitter, query_string))
            return 

    def make_endpoint_for_ssl_redirection(self, endpoint):
        if endpoint is not None:
            splited_endpoint = endpoint.split('.')
            return '.'.join(splited_endpoint[:2]) + '___' + splited_endpoint[2]

    def in_ssl_required_endpoint(self, endpoint):
        return self.make_endpoint_for_ssl_redirection(endpoint) in self.ssl_required_endpoints

    def wsgi_app(self, environ, start_response):
        self.debug_out.buf = StringIO()
        session = environ['beaker.session']
        #environ['abc'] = "AAA"
        self.debug_out.pprint(session)
        self.debug_out.pprint(environ)
        if self.config.get('SCRIPT_NAME') is not None:
            environ["SCRIPT_NAME"] = self.config.get('SCRIPT_NAME')
        result = Flask.wsgi_app(self, environ, start_response)
        self.debug_out.buf = None
        return result

    def __call__(self,environ, start_response):
        return Flask.__call__(self,environ, start_response)
        
    def init_middleware(self):
        session_opts = {
            'session.auto':True,
        }
        session_opts.update(self.config.get('BEAKER_SETTINGS',dict()))
        self.wsgi_app = self.session_middleware = SessionMiddleware(self.wsgi_app, config=session_opts)
        self.wsgi_app = SQLAlchemySessionMiddleware(self.wsgi_app, self)
        #self.middleware = SessionMiddleware(self.inner_call, config=session_opts)
        
##     def __init__(self, import_name, static_path=None):
##         super(CustomFlask,self).__init__(import_name, static_path=None)
##         self.config.__class__ = CustomConfig# = Config(self.root_path, self.default_config)
##         self.config.app = self

    def open_session(self, request):
        return getattr(request,'session', None)
        
    def save_session(self, session, response):
        return
        

def test():
    import memcache
    mc = memcache.Client(['127.0.0.1:11211'], debug=0)

    mc.set("some_key", "Some value")
    value = mc.get("some_key")

    mc.set("another_key", 3)
    mc.delete("another_key")

    mc.set("key", "1")   # note that the key used for incr/decr must be a string.
    mc.incr("key")
    mc.decr("key")

##     key = derive_key(obj)
##     obj = mc.get(key)
##     if not obj:
##         obj = backend_api.get(...)
##         mc.set(key, obj)



## session_store = FilesystemSessionStore()

## def application(environ, start_response):
##     request = Request(environ)
##     sid = request.cookie.get('cookie_name')
##     if sid is None:
##         request.session = session_store.new()
##     else:
##         request.session = session_store.get(sid)
##     response = get_the_response_object(request)
##     if request.session.should_save:
##         session_store.save(request.session)
##         response.set_cookie('cookie_name', request.session.sid)
##     return response(environ, start_response)
