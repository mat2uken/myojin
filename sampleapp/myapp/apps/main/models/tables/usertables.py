from .use_sqlalchemy import *

memo = Table(
    "memo", db.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('user_id', bigInteger, ForeignKey('user.id')),
    Column('text', UnicodeText(), default=u"", nullable=False,),
    Column('deleted', Boolean(), default=False),
    )

user = Table(
    "user", db.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('password', String(128), nullable=True),
    Column('email', String(255), unique=True, nullable=True),
    Column('new_email', String(255), default=None, nullable=True),
    Column('exit_email', String(255), default=None, nullable=True),
    Column('create_dt', DateTime(), default=datetime.now, nullable=False),
    Column('modify_dt', DateTime(), default=datetime.now, onupdate=datetime.now, nullable=False),
    Column('is_activated', Boolean(), default=False),
    Column('is_admin', Boolean(), default=False),
    Column('exit_advice', Unicode(500), default=None, nullable=True),
    Column('exit_dt', DateTime(), default=None),
    Column('deleted', Boolean(), default=False),
    )

image = Table(
    "image", db.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('name', UnicodeText()),
    Column('slug', UnicodeText()),
    Column('image', Binary),
    Column('alt_text', UnicodeText()),
    Column('deleted', Boolean(), default=False),
    )
