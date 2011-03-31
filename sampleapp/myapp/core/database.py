from .app import app
## from flaskext.sqlalchemy import SQLAlchemy


from sqlalchemy import orm
from sqlalchemy.orm.interfaces import SessionExtension
from sqlalchemy.orm import sessionmaker
import flaskext.sqlalchemy

class MySessionExtension(SessionExtension):
    def after_begin(self, session, transaction, connection):
        pass

    def after_rollback(self, session):
        pass
    def after_commit(self, session):
        pass
smaker = sessionmaker(extension=MySessionExtension(), autocommit=False,
                                                         autoflush=False,)
def _create_scoped_session(db):
    return orm.scoped_session(lambda: smaker(bind=db.engine))
## flaskext.sqlalchemy._create_scoped_session = _create_scoped_session
class CustomSQLAlchemy(flaskext.sqlalchemy.SQLAlchemy):
    def __init__(self,*args,**kws):
        super(CustomSQLAlchemy, self).__init__(*args,**kws)
        self.session = _create_scoped_session(self)

db = CustomSQLAlchemy(app)



import threading, thread, os
def _get_ident():
    return (thread.get_ident(), os.getpid())
threading._get_ident = _get_ident
from _threading_local import local
db.session.registry.registry = local()

db.session.extension = MySessionExtension()
app.db = db
def drop_all(self):
    from myojin.utils import drop_all_tables
    metadata = self
    return drop_all_tables(metadata, metadata.bind)

type(db.metadata).drop_all = drop_all
