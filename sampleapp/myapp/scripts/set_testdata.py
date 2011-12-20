# encoding: utf-8
from .. import app
from ..models import *
from myojin.utils import drop_all_tables

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
    first_user = User(email="mat2uken@cerevo.com", password='myojin').save()
    first_user.is_activated = True
    first_user.is_admin = True
    print "create second_user..."
    second_user = User(email="mat2uken+2@cerevo.com", password="myojin").save()
    second_user.is_activated = True    
    print "create myojin_user(inactive)..."
    myojin_user = User(email="myojindev@cerevo.com",password='myojin').save()
    for x in range(10):
        image = Image(name=u"name%s" % x, alt_text=u"")
        image.save()
    db.session.commit()

    for user in [first_user, second_user, myojin_user]:
        for x in range(7):
            Memo(user=user, text=u"%s" % x ).save()
    db.session.commit()
