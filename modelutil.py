# coding: utf-8
from __future__ import absolute_import
from myojin.funcutils import getattrs, setattrs
from sqlalchemy import UniqueConstraint, Table
from flask import current_app
from functools import wraps
from sqlalchemy.sql import Join
from sqlalchemy.orm.query import Query
from sqlalchemy.orm import exc as orm_exc

from myojin.converters import BaseModelConverter
from werkzeug.local import LocalProxy

from sqlalchemy.orm import class_mapper, object_session

from datetime import timedelta


class BaseModelType(type):
    def __init__(cls, name, bases, attrs):
        super(BaseModelType, cls).__init__(name, bases, attrs)
        if name == 'BaseModel':
            return
        BaseModel.classlist.append(cls)
        class ModelConverter(BaseModelConverter):
            HMAC_KEY = current_app.config['HMAC_KEY']
            query_arg_name = "query"
            model = cls
        current_app.url_map.converters[name] = ModelConverter

        BaseModel.models += (cls, )
        

def get_child_info(cls, mainattr, targetattrs):
    info = getattr(cls, '_child_info_cache', {}).get(mainattr, None)
    if not info:
        info = _get_child_info(cls, mainattr, targetattrs)
        if not hasattr(cls, '_child_info_cache'):
            cls._child_info_cache = dict()
        cls._child_info_cache[mainattr] = info
    return cls._child_info_cache[mainattr]
    
def _get_child_info(cls, mainattr, targetattrs):
    child_class = cls._sa_class_manager.mapper.get_property(mainattr).mapper.class_
    parent_cls =  reduce((lambda cls, attr:cls._sa_class_manager.mapper.get_property(attr).mapper.class_),
                         targetattrs.split("."), cls)
    props = { prop.mapper.class_:prop for prop in child_class._sa_class_manager.mapper.iterate_properties
              if getattrs(prop, 'mapper.class_', None)}
    return dict(child_class=child_class, targetattrs=targetattrs,
                to_parent_arg=props[parent_cls].key,
                to_cls_arg=props[cls].key)

def gen_children(self, mainattr, targetattrs):
    if not targetattrs:
        return
    cls = type(self)
    info = get_child_info(cls, mainattr, targetattrs)
    generated_children = gen_children_inner(self, mainattr, **info)
    return generated_children

def gen_children_inner(self, mainattr, child_class, targetattrs, to_parent_arg, to_cls_arg):
    target_parents = getattrs(self, targetattrs)
    generated_children = [child_class(**{to_parent_arg:parent, to_cls_arg:self}) for parent in target_parents]
    getattr(self, mainattr).extend(generated_children)


class NoneObject(): pass
from myojin.utils import encode_id, decode_id

from sqlalchemy import Table
from sqlalchemy.sql import and_

class CustomQuery(Query):
    def __init__(self, mapper, session=None, default_filter_name=None):
        self.default_filter_name = default_filter_name
        super(CustomQuery,self).__init__(mapper, session)
        assert not hasattr(self, "cls")
        self.cls = mapper.class_
        self.added_tables = frozenset(mapper.tables)
        self.filtered_tables = frozenset()
        
    def default_filter(self):
        filtered = reduce(lambda x, table:x.table2exp(table) ,self.added_tables, self)
        filtered.filtered_tables = self.filtered_tables | self.added_tables
        filtered.added_tables = frozenset()
        return filtered
    
    def join(self, *args, **kws):
        joined = super(CustomQuery,self).join(*args, **kws)
        tables = frozenset(y for x in joined._from_obj for y in [x.right, x.left] if isinstance(y, Table))
        joined.added_tables = tables - self.filtered_tables
        joined.filtered_tables = frozenset()
        return joined.default_filter()

    def table2exp(self, table):
        if not hasattr(table,'mapped_class'):
            print 'table',table
            print dir(table)
        return getattr(table.mapped_class, self.default_filter_name)(self, table)
    
    def get(self, id):
        return self.filter_by(id=id).first()
    default_filter_name = None

class QueryProperty(object):
    def __init__(self, query_cls, **kws):
        self.query_cls = query_cls
        self.kws = kws
        self.db = current_app.db
    def __get__(self, instance, owner):
        mapper = class_mapper(owner)
        return self.query_cls(mapper, self.db.session.registry(), **self.kws).default_filter()


from datetime import date, datetime
from functools import partial
class BaseModel(object):
    classlist = []
    __metaclass__ = BaseModelType
    __repratts__  = ()
    child_args = ()
    expiry_child_args = ()
    models = ()

    default_query_arg4converter = "query"
    @classmethod
    def init_after_map(cls):
        for x in cls.classlist:
            x.get_unique_columns()
            if isinstance(x.child_args, dict):
                for mainattr, targetattrs in x.child_args.items():
                    if targetattrs:
                        get_child_info(x, mainattr, targetattrs)


    @classmethod
    def get_unique_columns(cls):
        if hasattr(cls, '_unique_columns'):
            return cls._unique_columns
        table = cls._sa_class_manager.mapper.mapped_table
        if isinstance(table, Table):
            constraints = table.constraints
        elif isinstance(table, Join):
            constraints = table.left.constraints & table.right.constraints
        else:
            assert False

        names = [col.name.replace("_id","")
                 for constraint in constraints
                 if isinstance(constraint,UniqueConstraint)
                 for col in constraint .columns
                 if col.name.endswith("_id")
                 ]
        cls._unique_columns = names
        return names




    @classmethod
    def default_filter(cls, query, table):
        q = query.filter(~table.mapped_class.deleted)
        if 'expiry_date' not in table.c:
            return q
        return q.filter(table.c.expiry_date >= date.today() )

    @classmethod
    def default_user_filter(cls, query, table):
        q = cls.default_filter(query, table)
        if 'user_id' not in table.c:
            return q
        return q.filter(table.c.user_id== getattr(current_app.current_user, 'id', ()))
        
##     @classmethod
##     def join_with(cls, *args):
##         return join_with(*args)

    query = QueryProperty(CustomQuery, default_filter_name='default_filter')
    userquery = QueryProperty(CustomQuery, default_filter_name='default_user_filter')

    query_all = current_app.db.session.query_property()
    db = current_app.db
    def save(self):
        self.db.session.add(self)
        return self

    encode_salt = 47
    @property
    def encoded_id(self):
        return encode_id(self.id, self.encode_salt)
    @classmethod
    def decode_id(cls, s):
        return decode_id(s, cls.encode_salt)# = staticmethod(decode_id)
    @classmethod
    def get_by_encoded_id(cls, encoded_id, session=None):
        if not session:
            return cls.query.get(cls.decode_id(encoded_id))
        return session.query(cls).get(cls.decode_id(encoded_id))
    @classmethod
    def dummy_decode(cls, s):
        return s
    @staticmethod
    def init_basemodel(self, **kws):
        BaseModel.__init__(self, **kws)

    @staticmethod
    def kws_filter(modelClass, **kws):
        q = modelClass.query
        p = dict()
        for k, v in kws.items():
            if v is None:
                continue
            if v is NoneObject:
                v = None
            elif isinstance(v, (BaseModel, LocalProxy)):
                k += '_id'
                v = v.id
            p[k] = v
        return q.filter_by(**p)

    def __new__(cls, *args, **kws):
        if not args and not kws:
            return object.__new__(cls)
        names = cls.get_unique_columns()
        result = None
        if names and kws:
            q_kws = dict((k+"_id",v.id) if isinstance(v , BaseModel) else (k,v)
                for k,v in 
                kws.items() if k in names)
            if q_kws:
                q = cls.query_all.filter_by(**q_kws)
                result = q.first()

        if result:
            if not result.deleted:
                result.delete()
            result.deleted = False #result.regenerate()
            return result
        obj = object.__new__(cls, *args, **kws)
        return obj

    def __init__(self, **kws):
        kws.pop("self", None)
        kws.update(kws.pop("kws",{}))
        setattrs(self, kws)
        self.set_expiry_date()
        if isinstance(self.child_args, dict):
            for mainattr, targetattrs in self.child_args.items():
                gen_children(self, mainattr, targetattrs)
        self.set_expiry_date_children()
        #current_app.db.session.add(self)
        
    def __repr__(self):
        ks = self.__repratts__ 
        args = ",".join( _to_str(getattrs(self, k,None)) for k in ks[:5])
        return "<%s %2s %s>"%(type(self).__name__ , self.id, args)

    def delete(self):
        for arg in getattr(self,'child_args',()):
            for x in getattr(self, arg):
                x.delete()
        self.deleted = True

    def set_expiry_date(self, dt=None):
        from datetime import date
        from sqlalchemy.orm import class_mapper
        assert dt is None or hasattr(type(self), 'expiry_date')
        if hasattr(type(self), 'expiry_date'):
            old = self.expiry_date
            new = self.expiry_date = dt if dt else self.gen_expiry_date()
            if old != new:
                self.set_expiry_date_children()
            if self.expiry_date and self.expiry_date < date.today():
                self.delete()

        else:
            self.set_expiry_date_children()
    
    def set_expiry_date_children(self):
        for arg in self.expiry_child_args:
            xs = getattr(self, arg)
            if xs:
                for x in xs if hasattr(xs,'__iter__') else [xs]:
                    x.set_expiry_date()

    def regenerate(self):
        for arg in self.child_args:
            for x in getattr(self, arg):
                x.regenerate()
        self.deleted = False
        
def _to_str(x):
    if isinstance(x,(tuple, list)):
        return u"[%s]" % u", ".join((repr(str(y)) for y in x ))
    return str(x).replace('<','(').replace('>',')')
