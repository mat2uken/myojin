from .use_sqlalchemy import *

memo = Table(
    "memo_table", db.metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('user_table.id')),
    Column('text', UnicodeText(), default="", nullable=False,),
    Column('deleted', Boolean(), default=False),
    )

user = Table(
    "user_table", db.metadata,
    Column('id', Integer, primary_key=True),
#    Column('username', String(100), nullable=False, unique=True),
    Column('password', String(128), nullable=False),
    Column('email', String(256), nullable=True, unique=True), # TODO: 
    Column('new_email', String(256), default=None, nullable=True),
    Column('exit_email', String(256), default=None, nullable=True),
    Column('nickname', Unicode(50)),
    
    Column('last_upload_dt', DateTime(), default=datetime.now, nullable=False), # last upload file datetime
    Column('total_upload_size', BigInteger, default=0, nullable=False), # upload file size
    Column('month_upload_size', BigInteger, default=0, nullable=False), # upload file size
           
    Column('create_dt', DateTime(), default=datetime.now, nullable=False),
    Column('modify_dt', DateTime(), default=datetime.now, onupdate=datetime.now, nullable=False),
    Column('is_activated', Boolean(), default=False),
    Column('is_admin', Boolean(), default=False),
    
    Column('deleted', Boolean(), default=False),
    Column('notify', PickleType(), default=dict, nullable=False,),
    Column('config', PickleType(), default=dict, nullable=False,),

    Column('account_status', Integer, default=0),
    Column('last_login_dt', DateTime()),

    )
