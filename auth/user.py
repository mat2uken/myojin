# encoding: utf-8
from myojin.modelutil import BaseModel
from myojin.modelutil import QueryProperty, CustomQuery
from myojin.funcutils import keyword_only, caching
from myojin.mailutils import sendmail
from models import UserModelBase

from flask import current_app as app

import hashlib
from datetime import datetime

class InvalidActivationCode(Exception):
    pass
class RejectSns(Exception):
    def __init__(self, msg):
        self.msg = msg
class ExistsUser(Exception):
    def __init__(self, user):
        self.user = user
__all__ = ['InvalidActivationCode', 'RejectSns', 'ExistsUser']

class ActivableUserBase(UserModelBase):
    @property
    def expire_date(self):
        return datetime.now() + timedelta(hours=24)

    @property
    def url_expire_date(self):
        return expire_date().strftime("%Y%m%d%H%M%S")

    @property
    def display_expire_date(self):
        return expire_date().strftime('%Y/%m/%d %H:%M')

    def check_expire_date(self, expire_date):
        try:
            return datetime.strptime(expire_date, '%Y%m%d%H%M%S') > datetime.now()
        except ValueError as e:
            return False

    @property
    def get_email_template_path(filename):
        locale = babel.get_locale()
        language = locale.language
        return 'main/top/%s/%s' % (language[:2], filename)

    @property
    def activation_code(self):
        """
        ユーザーごとに持つアクティベーションコード
        """
        assert isinstance(self.id, (int, long))
        s = "%s$%s$%s$%s" % (self.salt, self.id, self.email, self.modify_dt.strftime("%Y%m%d%H%M%S"))
        return hashlib.sha1(s).hexdigest()

    def request_new_user_activation(self, password):
        """
        ユーザーにパスワードをセットしてアクティベーションメールを送信する
        """
        self.set_password(password)
        self.send_activation_email()

    def send_activation_email(self):
        """
        ユーザーのメールアドレスへアクティベーションメールを送信する
        """
        from boto.exception import BotoServerError
        self.db.session.commit()
        self.db.session.flush()
        try:
            sendmail(
                self.email,
                get_email_template_path('activation_mail.txt'),
                dict(
                    email=self.email,
                    token=self.activation_code,
                    url_expire_date=self.url_expire_date,
                    display_expire_date=self.display_expire_date))
        except BotoServerError as e:
            app.logger.error("ERROR USER %s" % self)
            app.logger.error(traceback.format_exc())
            error_msg = dict(
                MessageRejected=_('sns message reject'),
                InvalidParameterValue=_('sns invalid params')
            ).get(e.error_code, _('sns unknow error'))
            raise RejectSns(error_msg)
        app.logger.info('send_activation_email: to=>%s, token=>%s, url=>%s, expire_date=>%s' % (self.email, self.activation_code, self.url_expire_date, self.display_expire_date))

    def activate(self, activation_code, expire_date):
        """
        アクティベーションを試みる
        """
        if self.check_expire_date(expire_date):
            if activation_code == self.activation_code:
                self.is_activated = True
            else:
                app.logger.info('user activation code is invalid: user=>%s, activation_code=%s, self.activation_code=%s' % (self, activation_code, self.activation_code))
                raise InvalidActivationCode()
        else:
            app.logger.info('user activation code is expired: user=>%s' % self)
            raise InvalidActivationCode()

    def activate_email(self, email, token, expire_date):
        """
        メールアドレス変更したときのアクティベーション
        """
        self.activate(token, expire_date)
        self.email = email

    @classmethod
    def activate_by_email(cls, email, token, expire_date):
        """
        emailアドレスからユーザーを特定してアクティベーションを試みる
        """
        user = cls.unactivated_query.filter_by(email=email).first()
        if user is None:
            raise InvalidActivationCode()
        user.activate(token, expire_date)

    # classmethod filters
    @classmethod
    def default_filter(cls, query, table):
        return BaseModel.default_filter(query, table).filter_by(is_activated=True)

    @classmethod
    def default_unactivated_filter(cls, query, table):
        return BaseModel.default_filter(query, table).filter_by(is_activated=False)
    unactivated_query = QueryProperty(CustomQuery, default_filter_name='default_unactivated_filter')

    @classmethod
    def not_complete_user(cls, email):
        user = cls.query_all.filter_by(email=email).first()
        if user is not None:
            raise ExistsUser(user)
        else:
            return None
__all__ += ['ActivableUserBase']




def ConnectableUser(ActivatableUser):
    pass
