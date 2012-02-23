from ..... import db, app

from sqlalchemy import Table, Column
from sqlalchemy.schema import Index
from sqlalchemy.types import BigInteger, Integer, String, Unicode, UnicodeText, DateTime,Date, Boolean, PickleType, Text#, BIGINT
from sqlalchemy.types import LargeBinary, Binary
from sqlalchemy import ForeignKey
from sqlalchemy import func, Sequence
from sqlalchemy import ForeignKeyConstraint,UniqueConstraint
from datetime import datetime, date, timedelta
from sqlalchemy.sql.expression import desc
from sqlalchemy import schema
from myojin.sqlalchemyutil import EnumStatus
assert str(db.engine.url) != 'sqlite://', "must be initialized"

if db.engine.name == 'sqlite':
    BigInteger = Integer
    
def Index(*args, **kws):
    index = schema.Index(*args, **kws)
    db.metadata.__dict__.setdefault("index_list",[]).append(index)
