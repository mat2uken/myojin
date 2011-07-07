import datetime
from .tools import *
import flask
from flask import session

class AnonymousUser(object):
    username = 'anonymous'
    @classmethod
    def logout(cls):
        return
    def is_authenticated(self):
        return False
    
    def __nonzero__(self):
        return False

class UserModelBase(object):
    USER_ID_KEY = 'USER_ID'
    AnonymousUser = AnonymousUser
    @classmethod
    def current_user_getter(cls, f):
        cls.current_user_getter_func = staticmethod(f)
    
    @classmethod
    def current_user(cls):
        return cls.current_user_getter_func()
        
    @classmethod
    def logout(cls):
        session.flush()
        session._user = cls.AnonymousUser()
        session.modified = True

    @classmethod
    def get_user_id(cls):
        from flask.globals import _request_ctx_stack, request, current_app
##         if 'sid' in request.form or 'sid' in request.args:
##             Session = type(_request_ctx_stack.top.session)
##             sid = request.form.get('sid', request.args.get('sid', None))
##             if sid:
##                 arg_session = Session(dict(), id=sid, **current_app.session_middleware.options)
##                 arg_session.load()
##                 user_id = arg_session.get(cls.USER_ID_KEY, None)
##             else:
##                 user_id = None
##         else:
        form_session = getattr(session, '_form_session', None)
        user_id = (form_session or session).get(cls.USER_ID_KEY, None)
        return user_id

    @classmethod
    def get_current_user(cls):
        User = cls
        if hasattr(session,'_user' ):
            return session._user
        
        user_id = cls.get_user_id()
        if user_id is None:
            session._user = cls.AnonymousUser()
        else:
            user = User.query.get(user_id)
            session._user = user or cls.AnonymousUser()
        return session._user
    
    @property
    def password_check_result(self):
        return getattr(self,'_password_check_result',False)
    def login(self, *args, **kws):
        from flask.globals import _request_ctx_stack, request, current_app
        ## current_app.before_login(*args, **kws)
        
        assert self.password_check_result
        user = self
        from flask import session
        user.last_login = datetime.datetime.now()
        user.save()

        if self.USER_ID_KEY in session:
            if session[self.USER_ID_KEY] != user.id:
                # To avoid reusing another user's session, create a new, empty
                # session if the existing session corresponds to a different
                # authenticated user.
                session.flush()
        else:
            session.cycle_key()
        if hasattr(session, "_user"):
            delattr(session,"_user")
        session[self.USER_ID_KEY] = user.id

    def change_password(self, old_raw_password, new_raw_password):
        if self.check_password(old_raw_password):
            self.set_password(new_raw_password)
            return True
    def gen_hash_password(self, raw_password):
        import random
        from flask.globals import current_app
        algo = 'sha1'
        salt = current_app.config.get("SALT")
        if current.app.config.get("salt") is None:
            salt = get_hexdigest(algo, str(random.random()), str(random.random()))[:5]

        hsh = get_hexdigest(algo, salt, raw_password)
        return '%s$%s$%s' % (algo, salt, hsh)
        
    def set_password(self, raw_password):
        self.password = self.gen_hash_password(raw_password)
        return self
        
    def check_password(self, raw_password):
        if raw_password is None:
            return False
        result = check_password(raw_password, self.password)
        self._password_check_result = result
        return self._password_check_result
    
    def set_unusable_password(self):
        # Sets a value that will never be a valid hash
        self.password = UNUSABLE_PASSWORD
    def has_usable_password(self):
        return self.password != UNUSABLE_PASSWORD
    def is_authenticated(self):
        return True

    def make_random_password(self, length=10, allowed_chars='abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'):
        "Generates a random password with the given length and given allowed_chars"
        # Note that default value of allowed_chars does not have "I" or letters
        # that look like it -- just to avoid confusion.
        from random import choice
        return ''.join([choice(allowed_chars) for i in range(length)])

    @classmethod
    def authenticate(cls, username=None, password=None, email=None):
        User = cls
        user = None
        if username is not None:
            user = User.query.filter_by(username=username).first()
        elif email is not None:
            user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            return user
        return None

    def external_auth(self):
        self._password_check_result = True

    def external_login(self, *args, **kwargs):
        self.external_auth()
        self.login(*args, **kwargs)
