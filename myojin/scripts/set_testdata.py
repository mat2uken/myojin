# encoding: utf-8
import random

from datetime import datetime, date
from dateutil import relativedelta
from .. import app
from ..models import *
import os.path
from flaskext.utils import drop_all_tables    
def main():
    db.metadata.bind = db.engine
    db.metadata.drop_all()
    #drop_all_tables(db)
    
    db.metadata.create_all()

    # external sites
    #init_external()

    db.session.flush()
    # ユーザーの作成
    print "create first_user..."
    first_user = User(nickname=u"スーパーユーザー", email="mat2uken@cerevo.com", password='myojin',
                      memos = [Memo(text="abc"), Memo(text="AAAAA")]
                      ).save()
    first_user.is_activated = True
    first_user.is_admin = True
    print "create second_user..."
    second_user = User(nickname=u"テストユーザ", email="mat2uken+2@cerevo.com", password="myojin").save()
    second_user.is_activated = True    
    print "create myojin_user(inactive)..."
    myojin_user = User(nickname="myojin", email="myojindev@cerevo.com",password='myojin').save()
    db.session.commit()
    return
