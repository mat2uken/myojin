# encoding: utf-8

from flaskext.modelutil import BaseModel, QueryProperty, CustomQuery
## from .guest import *
from flaskext.funcutils import getattrs, setattrs, keyword_only
from ..... import db, app, debug
from flaskext.auth import UserModelBase
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

ACCOUNT_STATUS = ((0, u'未Activation'), (1, u'サービス利用中'), (2, u'退会'),)
def get_account_status_label(v):
    return ACCOUNT_STATUS[v][1]
def get_joined_service_status():
    return ACCOUNT_STATUS[1][0]
def get_withdrawal_service_status():
    return ACCOUNT_STATUS[2][0]
def set_not_activate_service_status():
    return ACCOUNT_STATUS[0][0]

class Memo(BaseModel, UserModelBase):
    @keyword_only
    def __init__(self, user=None, text=""):
        BaseModel.init_basemodel(
            self=self,
            user=user,
            text=text
            )

class User(BaseModel, UserModelBase):

##     def set_joined_service_status(self):
##         self.account_status = get_joined_service_status()
##     def set_withdrawal_service_status(self):
##         self.account_status = get_withdrawal_service_status()
##     def set_not_activate_service_status(self):
##         self.account_status = set_not_activate_service_status()

    def update_last_login_dt(self):
        self.last_login_dt = datetime.now()

    def after_login(self):
        self.update_last_login_dt()
        db.session.commit()

    def login(self):
        super(User, self).login()
        self.after_login()

##     @property
##     def abc(self):
##         return "HEELO"
    
##     @staticmethod
##     def reset_month_upload():
##         from myojin.apps.main.models.tables import user, basefile, shared_file, shared_event
##         if date.today().day != 1:
##             return
##         db.session.execute(
##             user.update().values(month_upload_size=0))
##         db.session.commit()

##     def gen_basefile_expiry_date(self, basefile=None):
##         if self.use_basefile_expiry:
##             return ((basefile.upload_date or date.today() )if basefile else date.today()) + self.basefile_expiry_td
##         return ETERNAL
        
##     def set_basefiles_expiry_date(self):
##         if self.use_basefile_expiry:
##             self.set_basefiles_expiry_date_with_delta(self.basefile_expiry_td)
##         else:
##             self.set_basefiles_expiry_date_with_ETERNAL()


##     @staticmethod
##     def delete_expired():
##         from myojin.apps.main.models.tables import user, basefile, shared_file, shared_event
##         db.session.execute(
##             tables.user.update().values(
##                 modify_dt=user.c.modify_dt,
##                 total_upload_size=(user.c.total_upload_size -
##                                    func.coalesce(
##                                    select(
##                                        [func.sum(func.coalesce(basefile.c.size,0))],
##                                        and_(
##                                            basefile.c.user_id == user.c.id,
##                                            basefile.c.expiry_date < date.today(),
##                                            basefile.c.deleted == False)
##                                        ).as_scalar()
##                                        , 0)
##                                    )
##                 )
##             )
##         db.session.commit()
##         for table in [basefile, tables.shared_event, tables.shared_file, tables.shared_guests_file,
##                       tables.shared_guests_clients_file]:
##             db.session.execute(
##                 table.update().where(
##                     and_(
##                         table.c.expiry_date < date.today(), table.c.deleted==False)
##                     ).values(deleted=True))
##             db.session.commit()
##     @staticmethod
##     def delete_nofile_event():
##         from myojin.apps.main.models.tables import user, basefile, shared_file, shared_event
##         file_exists = exists([shared_file.c.id],
##                        and_(
##                    shared_file.c.shared_event_id==shared_event.c.id,
##                    shared_file.c.expiry_date >= date.today(),
##                    shared_file.c.deleted==False
##                    )
##                    ).correlate(shared_event)

##         db.session.execute(
##             shared_event.update().where(
##                 and_(
##                     shared_event.c.deleted==False, ~file_exists
##                     )
##                 ).values(deleted=True))
##         db.session.commit()

##     @property
##     def max_upload(self):
##         if self.use_max_upload:
##             return self.user_type.config['max_upload']
##         return _Infinity

##     @property
##     def month_max_upload(self):
##         if self.use_month_max_upload:
##             return self.user_type.config['month_max_upload']
##         return _Infinity

##     @property
##     def use_max_upload(self):
##         return self.user_type.config.get('use_max_upload',False)

##     @property
##     def use_month_max_upload(self):
##         return self.user_type.config.get('use_month_max_upload',False)

##     def __new__(cls, *args, **kws): # important
##         return object.__new__(cls, *args, **kws)
    
##     def set_basefiles_expiry(self, filelimit):
##         self.use_basefile_expiry = 'UNLIMITED' != filelimit

##     def on_change_use_basefiles_expiry(self, old, new):
##         if app.config.get('SET_EXPIRY_WITH_SQL',False):
##             return self.set_basefiles_expiry_date()
##         from . import Basefile
##         if new:
##             for basefile in self.basefiles:
##                 basefile.set_expiry_date()
##         else:
##             for basefile in Basefile.get_today_upload_files():
##                 basefile.set_expiry_date(ETERNAL)

##     def on_change_basefiles_expiry_td(self, old, new):
##         if app.config.get('SET_EXPIRY_WITH_SQL',False):
##             return self.set_basefiles_expiry_date()
##         for basefile in self.basefiles:
##             basefile.set_expiry_date()
                
##     use_basefile_expiry = config_property('use_basefile_expiry', on_change=on_change_use_basefiles_expiry)
##     basefile_expiry_td = config_property('basefile_expiry_td', on_change=on_change_basefiles_expiry_td)

##     isset_filelimit = config_property('isset_filelimit')
    
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

    
    def gen_shared_file_expiry_date(self, shared_file=None):
        if not shared_file:
            return ETERNAL
        return shared_file.basefile.expiry_date # min(ETERNAL,shared_file.basefile.expiry_date)

    def get_invited_shared_events(self):
        from sqlalchemy import sql,and_,desc
        from sqlalchemy.orm import joinedload
        from myojin.models import SharedEvent,SharedFile
        shared_events = SharedEvent.query.join(
            SharedEvent.users_shared_guests_clients_in_folder).options(
            joinedload(SharedEvent.users_shared_guests_clients_in_folder),
            joinedload(SharedEvent.shared_folder),
            ).filter(sql.exists().where(
            and_(
                SharedEvent.id == SharedFile.shared_event_id,
                SharedFile.expiry_date >=  date.today(),
                ~SharedFile.deleted
                )
            )
                     ).order_by(desc(SharedEvent.id))
        return shared_events
        
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

    def change_nickname(self, new_nickname):
        self.nickname = new_nickname
        db.session.flush()
        return True

    @keyword_only
    def change_notify(self, announcement=None, 
                            pc_upload=None, pc_download=None,
                            nts_upload=None, nts_download=None,
                            post_success=None, post_fail=None):
        self.notify = dict(
          announcement = announcement if announcement is not None else self.notify['announcement'],
          pc_upload = pc_upload if pc_upload is not None else self.notify['pc_upload'],
          pc_download = pc_download if pc_download is not None else self.notify['pc_download'],
          nts_upload = nts_upload if nts_upload is not None else self.notify['nts_upload'],
          nts_download = nts_download if nts_download is not None else self.notify['nts_download'],
          post_success = post_success if post_success is not None else self.notify['post_success'],
          post_fail = post_fail if post_fail is not None else  self.notify['post_fail'],
        )
        db.session.commit()
        app.logger.debug('update user.notify: %s' % self.notify)
        return True

    def exit_complete(self, answer):
        exit_log = UserExit(user_id=self.id, answer=answer)
        exit_log.save()
        db.session.add(exit_log)
        self.account_status = get_withdrawal_service_status()
        self.exit_email = self.email
        self.email = None
        db.session.commit()
        self.delete()
        db.session.commit()
        return True

    
    def get_guests_with_client(self, client):
        from . import Guest, GuestsClient
        q = db.session.query(Guest).join(GuestsClient)
        return q.filter(
            Guest.user_id==self.id).filter(
            GuestsClient.client_id == client.id).filter(
                Guest.deleted==False).filter(
                    GuestsClient.deleted==False).distinct().order_by([Guest.kana, Guest.id])

    def create_shared_folder(self, **kws):
        from . import SharedFolder
        return SharedFolder(user=self, **kws)

    def get_address_list(self):
        from . import Guest, GuestsClient
        q = GuestsClient.query.outerjoin(Guest).filter(Guest.user==self).order_by([Guest.kana, Guest.id])
        q.options(contains_eager(GuestsClient.guest)).with_labels().order_by([Guest.nickname, GuestsClient.id])
        return q
    
    def get_address_each(self):
        from . import CLIENT_LIST
        ret = dict(zip(CLIENT_LIST, [[]] * len(CLIENT_LIST)))
        for guests_client in self.get_address_list():
            ret[guests_client.client.name].append(guests_client)
        return ret

    def add_address(self, nickname, email, kana, send_ntra):
        from . import Client, Guest, GuestsClient, CLIENT_NTRANSFER, CLIENT_PC
        return GuestsClient(
            guest=Guest(user=self, nickname=nickname, email=email, kana=kana),
            client=Client.query.filter_by(name=CLIENT_NTRANSFER if send_ntra else CLIENT_PC).first()
            )

    def get_recent_news(self, count=None):
        from . import UserNews, USER_RECENT_LIMIT
        if count is None:
            count = USER_RECENT_LIMIT
        news = BaseModel.kws_filter(UserNews, to_user=self).order_by(desc(UserNews.create_dt))[:count]
        if len(news) == 0:
            return news
        for x in xrange(USER_RECENT_LIMIT - len(news)):
            news.append(None)
        return news

    def download_files(self, basefiles, who=None, filename_encoding=None):
        assert self.is_authenticated() or who and who.is_authenticated() # TODO raise

        basefiles = [basefile for basefile in basefiles]
        for basefile in basefiles:
            assert self is basefile.user

        if len(basefiles) == 1:
            return basefiles[0].send_file(as_attachment=True)

        from flask import request
        import httpagentparser
        if not filename_encoding:
            try:
                ua = httpagentparser.detect(request.environ.get('HTTP_USER_AGENT', ''))
                filename_encoding = 'ms932' if ua['os'] and 'Win' in ua['os']['name'] else 'utf-8'
            except:
                filename_encoding = 'utf-8'
        from flaskext.send_zip import send_zip
        filename_path_list_first = [
            (bf.filename.encode(filename_encoding), bf.path)
            for bf in basefiles]
        # ファイル名が重複する場合は、ファイル名を変更して対処
        filename_count = {}
        for fname, fpath in filename_path_list_first:
            filename_count[fname] = filename_count.setdefault(fname, 0) + 1
        filename_path_list = []
        import os.path
        for fname, fpath in filename_path_list_first:
            def check_and_rename(p):
                c = filename_count.get(p, 0)
                if  c > 1:
                    base, ext = os.path.splitext(p)
                    try:
                        base, suffix = base.rsplit('_')
                        suffix = int(suffix)
                        if suffix > 10:
                            p = '%s_%s%s' % (base+'_'+suffix, c-1, ext)
                        else:
                            p = '%s_%s%s' % (base, c-1, ext)
                    except (TypeError, ValueError) as e:
                        p = '%s_%s%s' % (base, c-1, ext)
                    return check_and_rename(p)
                else:
                    return p
            p = check_and_rename(fname)
            filename_count[fname] -= 1 
            filename_path_list += [(p, fpath)]

        zipfilename = '%s_%s.zip' % (datetime.now().strftime(format='%Y%m%d'), len(basefiles))
        return send_zip(zipfilename, filename_path_list)
    class UploadSizeLimitException(Exception):
        pass

    def _upload_size_reset_check(self):
        now = datetime.now()
        
        last = self.last_upload_dt
        if (now.year, now.month ) != (last.year, last.month):
            self.month_upload_size = 0 # reset
    def get_upload_limit(self):
        return min(self.max_upload - self.total_upload_size, self.month_max_upload - self.month_upload_size)

    def check_upload_size(self, size): # called from Basefile.create
        self._upload_size_reset_check()
        self.total_upload_size += size
        self.month_upload_size += size
        return (self.total_upload_size <= self.max_upload and
                self.month_upload_size <= self.month_max_upload)

    def decrement_size(self,basefile):
        self.total_upload_size -= (basefile.size or 0)
        
    def upload(self, filename, file):
        from . import Basefile
        basefile = Basefile.create(
            filename=filename, file=file,
            user=self)
        return basefile

    def download_shared_files(self, shared_filesn):
        return self.download_files([x.basefile for x in shared_files])

    def some_shared_me_now(self):
        return self.get_invited_shared_events().count()

    def is_checked_send_ntr(self):
        return self.config.get('send_ntr_checked',False)

    def set_checked_send_ntr(self, checked):
        self.config['send_ntr_checked'] = checked
        ##assert self.config['send_ntr_checked']
        db.session.flush()

    def get_user_service(self, name=None):
        from .external_site import ExternalSite, UserService
        from myojin import current_user
        from sqlalchemy.orm import joinedload
        sites = ExternalSite.query.options(joinedload('users_user_service'))
        if name is not None:
            sites = sites.filter(ExternalSite.name==name)
            return sites.all()[0]
        else:
            return sites.all()

__all__ = ['User', 'Memo']
