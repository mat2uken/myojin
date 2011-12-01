# encoding: utf-8
from flask import Flask, Request#, Session
import flask


from werkzeug.contrib.sessions import FilesystemSessionStore
SESSION_KEY = "HOGE"
import werkzeug.contrib.sessions#.Session
#class Session(flask.Session):
#from flaskext.auth import CustomRequest
from flask import Flask, Request#, Session
import flask

import threading
from cStringIO import StringIO
from flask import Config
from pprint import pprint
from beaker.middleware import SessionMiddleware
from beaker.session import SessionObject
import beaker.session
import beaker.middleware

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

    @property
    def is_smart(self):
        ret = getattr(self, '_is_smart', None)
        if ret is None:
            def _is_smart_():
                ua = self.environ.get('HTTP_USER_AGENT', None)
                if ua is not None:
                    self.ua = ua
                    return mobile_re.match(ua.lower()) is not None
            self._is_smart = _is_smart_()
            ret = self._is_smart
        return ret

    def _is_find_ua(self, string):
        ret = getattr(self, string, None)
        if ret is None:
            ua = self.environ.get('HTTP_USER_AGENT', None)
            self.ua = ua
            ret = False if ua is None else ua.lower().find(string) > -1
            setattr(self, '_is_' + string, ret)
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

from datetime import datetime, timedelta
import random
import time
#from beaker.session import getpid
from os import getpid
from beaker.crypto import hmac as HMAC, hmac_sha1 as SHA1, md5
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
                self.__dict__['_sess'] = beaker.session.CookieSession(req, **params)
            else:
                self.__dict__['_sess'] = CustomBeakerSession(req, use_cookies=True,
                                                 **params)
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

class Session(werkzeug.contrib.sessions.Session):
    def flush(self):
        from flask.globals import _request_ctx_stack
        _request_ctx_stack.top.session = session_store.new()

    def cycle_key(self):
        self.sid = session_store.generate_key()
        self.modified = True

session_store = FilesystemSessionStore(session_class=Session)
COOKIE_NAME = 'C'
import os
class SQLAlchemySessionMiddleware(object):
    def __init__(self,app, flask_app):
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


class CustomFlask(Flask):
    debug_out = Debug()
    request_class = CustomRequest
    session_store = session_store
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
            if not app.is_ssl_request() and request.endpoint in app.ssl_required_endpoints:
                server_name = (
                    app.config['SERVER_NAME'] or environ.get('HTTP_HOST') or environ.get('SERVER_NAME')
                    ).split(":")[0]

                query_string = environ.get('QUERY_STRING', '')
                query_splitter = "?" if query_string else ""
                path_info = request.environ['PATH_INFO']
                return redirect("https://%s%s%s%s" % (server_name, path_info, query_splitter, query_string))
            return 
        
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
        from myojin.applogging import initlogging
        initlogging(self)
        session_opts = {
            #'session.type':'ext:memcached',
            #'session.type':'file',
            'session.auto':True,
            
            #'session.lock_dir': '/tmp/container_mcd_lock',
            #'session.cookie_expires':True,
            #'session.encrypt_key':'',
            #'session.validate_key':'HOKARIHOKARI',
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
##         self.debug_out.buf = StringIO()
        return getattr(request,'session', None)
        
        sid = request.cookies.get(COOKIE_NAME)
        if sid is None:
            if 'sid' in request.form:
                return session_store.get(request.form['sid'])
            else:
                return session_store.new()
        else:
            return session_store.get(sid)
        
        
    def save_session(self, session, response):
##         self.debug_out.buf = None
        return
        if session.should_save:
            session_store.save(session)
            response.set_cookie(COOKIE_NAME, session.sid)
        #return response(environ, start_response)
        
    


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
