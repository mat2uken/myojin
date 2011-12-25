# encoding: utf-8
import hashlib
from datetime import datetime
from myojin.modelutil import BaseModel, QueryProperty, CustomQuery
from myojin.funcutils import keyword_only
from myojin.auth import UserModelBase
from myojin.mailutils import sendmail
from ..... import db, app

def _check_expire_date(expire_date):
    return datetime.strptime(expire_date, '%Y%m%d%H%M%S') > datetime.now()

class Memo(BaseModel):
    @keyword_only
    def __init__(self, user=None, text=""):
        BaseModel.init_basemodel(
            self=self,
            user=user,
            text=text
            )

class Image(BaseModel):
    def __init__(self, *args, **kws):
        BaseModel.init_basemodel(**locals())

class User(BaseModel, UserModelBase):

    @keyword_only
    def __init__(self, email, password=None, is_activated=False):
        BaseModel.init_basemodel(
            self=self,
            email=email,
            is_activated=is_activated,
            )
        if password:
            self.set_password(password)
        else:
            self.set_unusable_password()
        
    __repratts__  = ('email',)

    salt = "AnjbRbAeiPdib"

    @classmethod
    def default_filter(cls, query, table):
        return BaseModel.default_filter(query, table).filter_by(is_activated=True)

    @classmethod
    def default_unactivated_filter(cls, query, table):
        return BaseModel.default_filter(query, table).filter_by(is_activated=False)
    
    unactivated_query = QueryProperty(CustomQuery, default_filter_name='default_unactivated_filter')

    @classmethod
    def activate_user(cls, email, token, expire_date):
        user = cls.unactivated_query.filter_by(email=email).first()
        if user is not None and user.activate(token, expire_date):
            pass
        else:
            raise InvalidActivationCode()

    def activate_email(self, email, token, expire_date):
        if self.activate(token, expire_date):
            self.email = email
        else:
            raise InvalidActivationCode()

    @classmethod
    def not_complete_user(cls, email):
        user = cls.query_all.filter_by(email=email).first()
        if user is not None:
            raise ExistsUser(user)
        else:
            return None

    @property
    def activation_code(self):
        assert isinstance(self.id, (int, long))
        s = "%s$%s$%s$%s" % (self.salt, self.id, self.email, self.modify_dt.strftime("%Y%m%d%H%M%S"))
        return hashlib.sha1(s).hexdigest()

    def activate(self, activation_code, expire_date):
        if _check_expire_date(expire_date):
            if activation_code == self.activation_code:
                self.is_activated = True
                return
            else:
                raise InvalidActivationCode()
        else:
            raise InvalidActivationCode()

    def goodbye(self, advice):
        self.exit_email = self.email
        self.email = None
        self.exit_advice = advice
        self.deleted = True
        self.exit_dt = datetime.now()

    def is_unique_email(self, email):
        if self.email != email:
            return User.query_all.filter(User.email==email).count() == 0
        return True

@UserModelBase.current_user_getter
def get_current_user():
    return User.get_current_user()

class InvalidActivationCode(Exception): pass
class ExistsUser(Exception):
    def __init__(self, user):
        self.user = user

__all__ = ['User', 'Memo', 'Image', 'InvalidActivationCode', 'ExistsUser']
