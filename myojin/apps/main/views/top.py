# encoding: utf-8

import datetime
from myojin import app
from flaskext import submodule, utils as flaskext_utils

from flask import request, session, make_response
from flaskext.utils import redirect, redirect_to
module = submodule.SubModule(__name__, url_prefix="")
from ..models import User
from flask import url_for

@module.route('/')
@module.templated()
def index():
    return dict()

@module.route('/users')
def users():
    users = User.query.all()
    print users
    user_links = "<br/>".join(
        '<a href="%s">%s</a>   <a href="%s">%s</a>  <a href="%s">%s</a>' % (
            url_for("main.top.user", user=user),
            url_for("main.top.user", user=user),
            url_for("main.top.user_by_id", user=user),
            url_for("main.top.user_by_id", user=user),
            url_for("main.top.user_by_token", user=user),
            url_for("main.top.user_by_token", user=user),
            
            )
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
    return "hello2"

@module.route('/user/id/<User(attr=id):user>')
def user_by_id(user):
    return user.nickname

@module.route('/user/id/<User(tokenkind=fileupload, minutes=1):user>')
def user_by_token(user):
    return user.nickname



from flaskext.rum import rum_response
from myojin.core.decorators import admin_required, admin_ip_check

@module.route('/admin', methods=('GET','POST'), decorators=(admin_required(),))
@module.route('/admin/<emptiable_path:path>', methods=('GET','POST'), strict_slashes=False)
def admin(path=""):
    models = [User]
    return rum_response(path, models)

from rum import fields

from sqlalchemy.orm import class_mapper, object_session


fields.FieldFactory.fields(User, (
    'email',
    'is_activated',
    'is_admin',
    'deleted',
        ))
from flaskext.wtf import Form, TextField, TextAreaField, QuerySelectField, QuerySelectMultipleField, PasswordField, FileField, BooleanField, SelectField, RadioField, HiddenField
class AdminLogin(Form):
    email = TextField(u'Email')
    password = PasswordField(u'Password')
    
@module.route('/adminlogin', methods=('GET', 'POST',))
@module.with_form(AdminLogin)
@module.templated()
def adminlogin(form=None, email=None, password=None):
    print "RESULT:", request.method.upper(),form.validate()
    if 'POST' == request.method.upper() and form.validate():
        user = User.authenticate(email=email,password=password)
        print "user:",user
        if user:
            user.login()
            if user.is_admin:
                return redirect_to('main.top.admin')
            else:
                return redirect_to('main.top.index')
    return dict(form=form)

@module.route('/logout')
@module.templated("/main/top/logout.html")
def logout():
    User.logout()
    return redirect_to('main.top.index')
