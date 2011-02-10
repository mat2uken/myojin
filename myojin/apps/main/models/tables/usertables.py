from .use_sqlalchemy import *

# 2010/11/26
# postgresql: alter table user_type_table add column deleted boolean;
user_type = Table(
    "user_type_table", db.metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(100), nullable=False, unique=True, index=True),
    Column('config', PickleType(), default=dict, nullable=False,),
    Column('deleted', Boolean(), default=False),
)

# 2010/11/30
# postgresql: alter table user_exit_table add column exit_dt timestamp without time zone;
# postgresql: update user_exit_table set exit_dt=now();
# postgresql: alter table user_exit_table alter column exit_dt set not null;
# 2010/11/26
# postgresql: alter table user_exit_table add column deleted boolean;
user_exit = Table(
    "user_exit_table", db.metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('user_table.id')),
    Column('answer', PickleType(), default=dict, nullable=False,),
    Column('exit_dt', DateTime(), default=datetime.now, nullable=False),
    Column('deleted', Boolean(), default=False),
    )

# 2010/12/13
# postgresql: alter table user_table add column account_status smallint;
# postgresql: alter table user_table alter column account_status set default 0;
# postgresql: update user_table set account_status=0;
# postgresql: alter table user_table alter column account_status set not null;

# postgresql: alter table user_table add column last_login_dt timestamp without time zone;


# 2010/12/01
# postgresql: alter table user_table alter column email type varchar(256);
# postgresql: alter table user_table alter column new_email type varchar(256);
# postgresql: alter table user_table alter column exit_email type varchar(256);
# 2010/11/29
# postgresql: alter table user_table add column month_upload_size bigint;
# postgresql: alter table user_table alter column month_upload_size set default 0;
# postgresql: update user_table set month_upload_size=0;
# postgresql: alter table user_table alter column month_upload_size set not null;
# 2010/11/25
# postgresql: alter table user_table drop username;
# postgresql: alter table user_table drop column notify_upload;
# postgresql: alter table user_table drop column notify_download;
# postgresql: alter table user_table add column notify BYTEA;
user = Table(
    "user_table", db.metadata,
    Column('id', Integer, primary_key=True),
#    Column('username', String(100), nullable=False, unique=True),
    Column('password', String(128), nullable=False),
    Column('email', String(256), nullable=True, unique=True), # TODO: 
    Column('new_email', String(256), default=None, nullable=True),
    Column('exit_email', String(256), default=None, nullable=True),
    Column('nickname', Unicode(50)),
    
    Column('user_type_id', Integer, ForeignKey('user_type_table.id')),
    Column('last_upload_dt', DateTime(), default=datetime.now, nullable=False), # last upload file datetime
    Column('total_upload_size', BigInteger, default=0, nullable=False), # upload file size
    Column('month_upload_size', BigInteger, default=0, nullable=False), # upload file size
           
    Column('create_dt', DateTime(), default=datetime.now, nullable=False),
    Column('modify_dt', DateTime(), default=datetime.now, onupdate=datetime.now, nullable=False),
    Column('is_activated', Boolean(), default=False),
    Column('is_admin', Boolean(), default=False),
    
    Column('deleted', Boolean(), default=False),
#    Column('notify_upload', Boolean(), default=False),
#    Column('notify_download', Boolean(), default=False),
    Column('notify', PickleType(), default=dict, nullable=False,),
    Column('config', PickleType(), default=dict, nullable=False,),

    Column('account_status', Integer, default=0),
    Column('last_login_dt', DateTime()),

    )
