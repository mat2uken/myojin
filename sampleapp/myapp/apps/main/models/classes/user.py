# encoding: utf-8

from myojin.modelutil import BaseModel, QueryProperty, CustomQuery
## from .guest import *
from myojin.funcutils import getattrs, setattrs, keyword_only
from ..... import db, app
from myojin.auth import UserModelBase
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import contains_eager
from sqlalchemy.sql.expression import desc, distinct
import hashlib
from datetime import datetime, date, timedelta

def gen_initial_user_types():
    return dict(default=dict(
        use_basefile_expiry=True,
        basefile_expiry_td=timedelta(days=7),
        max_upload=2000,
        use_max_upload=False,
        month_max_upload=2000,
        use_month_max_upload=False,
        isset_filelimit=False,
        ))


ETERNAL = date(3000,1,1)
def is_eternal(dt):
    return dt >= ETERNAL
    
from .. import tables
from sqlalchemy.sql import func,select,and_, exists
from decimal import _Infinity

class Memo(BaseModel, UserModelBase):
    @keyword_only
    def __init__(self, user=None, text=""):
        BaseModel.init_basemodel(
            self=self,
            user=user,
            text=text
            )

class User(BaseModel, UserModelBase):

    def update_last_login_dt(self):
        self.last_login_dt = datetime.now()

    def after_login(self):
        self.update_last_login_dt()
        db.session.commit()

    def login(self):
        super(User, self).login()
        self.after_login()

    
    @keyword_only
    def __init__(self, email, nickname, password=None, is_activated=False, config=None, memos=None):
        BaseModel.init_basemodel(
            self=self,
            config=config or dict(),
            email=email,
            memos=memos or [],
            nickname=nickname,
            is_activated=is_activated,
            )
        assert password
        if password:
            self.set_password(password)
        else:
            self.set_unusable_password()
        # set default notify
        self.notify = dict(announcement=True,
                           pc_upload=True, pc_download=True,
                           nts_upload=True, nts_download=True,
                           post_success=True, post_fail=True)

        
    __repratts__  = ('nickname',)
    child_args = ('shared_folders', 'basefiles', 'user_news',)

    salt = "AnjbRbAeiPdib"
    @classmethod
    def default_filter(cls, query, table):
        return BaseModel.default_filter(query, table).filter_by(is_activated=True)

    @classmethod
    def default_unactivated_filter(cls, query, table):
        return BaseModel.default_filter(query, table).filter_by(is_activated=False)
    
    unactivated_query = QueryProperty(CustomQuery, default_filter_name='default_unactivated_filter')

    @property
    def activation_code(self):
        assert isinstance(self.id, (int, long))
        s = "%s$%s$%s$%s$%s" % (self.salt, self.id, self.nickname,self.email,self.modify_dt.strftime("%Y%m%d%H%M%S"))
        return hashlib.sha1(s).hexdigest()
        modify_dt
        return "todo:make:hash:%s" % self.id

    def activate(self, activation_code):
        assert isinstance(activation_code, basestring)
        if isinstance(activation_code,unicode):
            activation_code = activation_code.encode("utf-8")
        if activation_code == self.activation_code:
            self.is_activated = True
            self.account_status = get_joined_service_status()
            self.save()
            db.session.add(self)
            db.session.commit()
            return True
        return False

    def set_new_email(self, new_email, raw_password):
        if self.check_password(raw_password):
            unique = self.query.filter_by(email=new_email).first()
            if unique is None:
                self.new_email = new_email
                self.save()
                db.session.add(self)
                db.session.commit()
                return True
            else:
                return False
        else:
            return False

    def activate_new_email(self, activation_code):
        if self.new_email is not None:
            if self.activate(activation_code):
                self.email = self.new_email
                self.new_email = None
                db.session.flush()
                return True
            else:
                return False
        else:
            return False

@UserModelBase.current_user_getter
def get_current_user():
    return User.get_current_user()

class Image(BaseModel):
    def __init__(self, *args, **kws):
        BaseModel.init_basemodel(**locals())

__all__ = ['User', 'Memo', 'Image']
