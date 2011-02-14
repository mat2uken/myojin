from sqlalchemy.orm import mapper, relation
from sqlalchemy import select
from sqlalchemy import and_,not_
from ..tables import *
from ..classes import *
from sqlalchemy.ext.associationproxy import association_proxy
from datetime import date, timedelta

from sqlalchemy.orm import mapper, relation, backref
import sqlalchemy.orm
from sqlalchemy import select
from sqlalchemy import and_,not_
from ..tables import *
from ..classes import *
#from .tools import *
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.interfaces import MapperExtension
def mapper(*args, **kws):
    if 'extension' not in kws:
        print args[0]
    return sqlalchemy.orm.mapper(*args, **kws)
class MyojinMapperExt(MapperExtension):
    def instrument_class(self, mapper, class_):
        if mapper.non_primary:
            return
        mapper.local_table.mapped_class = class_
    
