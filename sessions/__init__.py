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

class CustomRequest(Request):
    def __init__(self, environ):
        super(CustomRequest,self).__init__(environ)
        if 'beaker.session' in environ:
            self.session = environ['beaker.session']
from datetime import datetime, timedelta
import random
import time
from beaker.session import getpid
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
class CustomFlask(Flask):
    debug_out = Debug()
    request_class = CustomRequest
    session_store = session_store
    def __init__(self, *args, **kws):
        super(CustomFlask,self).__init__(*args, **kws)
        self.app = self
        from flask.globals import _request_ctx_stack
        _request_ctx_stack.push(self)
    def wsgi_app(self, environ, start_response):
        self.debug_out.buf = StringIO()
        session = environ['beaker.session']
        #environ['abc'] = "AAA"
        self.debug_out.pprint(session)
        self.debug_out.pprint(environ)
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