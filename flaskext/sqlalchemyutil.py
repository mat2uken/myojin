# encoding: utf-8
from __future__ import absolute_import # import sqlalchemyが衝突するので
mod_sqlalchemy_sql =  __import__('sqlalchemy.sql', {}, {}, [''])
mod_sqlalchemy_expression = getattr(mod_sqlalchemy_sql, 'expression')
between = getattr(mod_sqlalchemy_expression, 'between')
case = getattr(mod_sqlalchemy_expression, 'case')
func = getattr(mod_sqlalchemy_sql, 'func')
select = getattr(mod_sqlalchemy_sql, 'select')
and_ = getattr(mod_sqlalchemy_sql, 'and_')

def get_sum_by_case(cases):
    ret = []
    for (whens, then, else_,) in cases:
        ret.append(
            func.sum(case(
                [(whens, then)],
                else_=else_
            ))
        )
    return ret

def get_sum_by_case_query(cases, wheres):
    q = select(get_sum_by_case(cases)).where(and_(*wheres))
    return q

from sqlalchemy import types

class EnumStatus(types.TypeDecorator):
    impl = types.Integer
    def __init__(self, status_names, *arg, **kws):
        types.TypeDecorator.__init__(self, *arg, **kws)
        self.status_names = status_names
        self.int2name = dict(enumerate(status_names))
        self.name2int = dict((v,k) for k,v in enumerate(status_names))

    def process_bind_param(self, value, dialect):
        assert isinstance(value, basestring), repr(value)
        return self.name2int[value]

    def process_result_value(self, value, dialect):
        assert isinstance(value, (int,long))
        return self.int2name[value]

