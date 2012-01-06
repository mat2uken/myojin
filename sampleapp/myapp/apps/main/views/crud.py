# encoding: utf-8

import datetime
from myojin import submodule, utils as flaskext_utils
from myojin.rum import rum_response
from ....core.decorators import admin_required, login_required
from .... import current_app
from flask import request, session, make_response, app
from myojin.utils import redirect, redirect_to
module = submodule.SubModule(__name__, url_prefix="/crud")
from ..models import User, Memo
from flask import url_for

from tw.forms.samples import AddUserForm
test_form = AddUserForm('mytest')

from tw.api import make_middleware

current_app.wsgi_app = make_middleware(current_app.wsgi_app, stack_registry=True)

# トップ画面。
@module.route('/')
@module.templated() # @module.templated('index.html')と同様。templates/main/top/index.htmlが使用される。
def index():
    return dict(test_form=test_form)
    #return "hello"
test_json = """
{
  "page": "1",
  "records": "10",
  "total": "2",
  "rows": [
      {
          "id": 3,
          "cell": [
              3,
              "cell 1",
              "2010-09-29T19:05:32",
              "2010-09-29T20:15:56",
              "hurrf",
              "0" 
          ] 
      },
      {
          "id": 1,
          "cell": [
              1,
              "teaasdfasdf",
              "2010-09-28T21:49:21",
              "2010-09-28T21:49:21",
              "aefasdfsadf",
              "1" 
          ] 
      } 
  ]
  }
  """

from . import forms
from json import dumps
import math
from pprint import pprint 
@module.route('/getrows')
@module.with_form(forms.JqGridForm)
def getrows(form=None, search=False, rows=None, page=None, sidx=None, sord=None,filters=None):
    print '====== start'
    pprint(filters)
    print '====== end'
    start = (page - 1) * rows
    end = start + rows
    print locals()
    rows_data = [
        dict(id=x.id, cell=[x.id,x.user.nickname, x.text,"<h1>abc</h1>"])
        for x in 
        Memo.query[start:end]]
    total = int(math.ceil(Memo.query.count() / float(rows)))
    data = dict(
        page=page,
        total=total,
        rows=rows_data,
        records=len(rows_data))
    return dumps(data)
    return test_json
    return "{}"


"/crud/getrows?model=Wine&_search=false&nd=1302242119887&rows=10&page=1&sidx=provider&sord=asc"


