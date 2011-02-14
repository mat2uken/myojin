# encoding: utf-8

import datetime
from flaskext import submodule, utils as flaskext_utils
from flaskext.rum import rum_response
from myojin.core.decorators import admin_required, admin_ip_check, login_required
from myojin import current_user
from flask import request, session, make_response
from flaskext.utils import redirect, redirect_to
module = submodule.SubModule(__name__, url_prefix="")
from ..models import User, Memo
from flask import url_for

# トップ画面。
@module.route('/')
@module.templated() # @module.templated('index.html')と同様。templates/main/top/index.htmlが使用される。
def index():
    return dict()

# Userの一覧とリンクを表示
@module.route('/users')
def users():
    users = User.query.all()
    print users
    user_links = "<br/>".join(
        '<a href="%s">%s</a>   <a href="%s">%s</a>  <a href="%s">%s</a>' % (
            url_for("main.top.user", user=user), url_for("main.top.user", user=user),
            url_for("main.top.user_by_id", user=user), url_for("main.top.user_by_id", user=user),
            url_for("main.top.user_by_token", user=user), url_for("main.top.user_by_token", user=user),)
        for user in users)
    return """<html>
    <body>
    hello<br/>
    %s
    </body>
    </html>""" % user_links

@module.route('/user/<User:user>')
def user(user):
    return user.nickname

@module.route('/user/id/<User(attr=id):user>')
def user_by_id(user):
    return user.nickname

# 有効期限付きトークンを服務URLにマッチします。
# tokenkindは、トークンの種別を示す任意の名前です。
# 他のtokenkindと重複しない任意の名前を使用してください。
# minutesは有効期限を分単位で記述します。
# myojin/flaskext/converters.py のBaseModelConverterを参照してください。
@module.route('/user/id/<User(tokenkind=user_by_token, minutes=1):user>')
def user_by_token(user):
    return user.nickname

# adminユーザログインフォーム
from flaskext.wtf import Form, TextField, TextAreaField, QuerySelectField, QuerySelectMultipleField, PasswordField, FileField, BooleanField, SelectField, RadioField, HiddenField
class AdminLogin(Form):
    email = TextField(u'Email')
    password = PasswordField(u'Password')
    
@module.route('/login', methods=('GET', 'POST',))
@module.with_form(AdminLogin) #AdminLoginフォームを使用。emailとpasswordとformが引数に渡されます。
@module.templated('adminlogin.html')
def login(form=None, email=None, password=None):
    if 'POST' == request.method.upper() and form.validate():
        user = User.authenticate(email=email,password=password)
        if user:
            user.login() # ログインします。（セッションにセット）
            return redirect_to('main.top.index')
    return dict(form=form)

## adminユーザログイン
@module.route('/adminlogin', methods=('GET', 'POST',))
@module.with_form(AdminLogin) #AdminLoginフォームを使用。emailとpasswordとformが引数に渡されます。
@module.templated()
def adminlogin(form=None, email=None, password=None):
    if 'POST' == request.method.upper() and form.validate():
        user = User.authenticate(email=email,password=password)
        if user:
            user.login() # ログインします。（セッションにセット）
            if user.is_admin:
                return redirect_to('main.top.admin')
            else:
                return redirect_to('main.top.index')
    return dict(form=form)

## ログアウト
@module.route('/logout')
@module.templated("/main/top/logout.html")
def logout():
    User.logout()
    return redirect_to('main.top.index')

@module.route('/home')
@login_required()
def userhome():
    user = current_user
    memos = Memo.userquery.all()
    m = "<br/>".join(memo.text for memo in memos)
    return user.nickname + '<br/>'+ m

## 管理画面。Rumを使用。
@module.route('/admin', methods=('GET','POST'), decorators=(admin_required(),))
@module.route('/admin/<emptiable_path:path>', methods=('GET','POST'), strict_slashes=False)
def admin(path=""):
    models = [User] # 管理画面に表示するモデルを指定
    return rum_response(path, models)




from rum import fields
## 管理画面で表示するカラムを指定
fields.FieldFactory.fields(User, (
    'email',
    'is_activated',
    'is_admin',
    'deleted',
        ))
