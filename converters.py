# coding: utf-8
from __future__ import absolute_import
from werkzeug.routing import AnyConverter,PathConverter
from werkzeug.urls import url_encode, url_quote
import functools
from importlib import import_module
from sqlalchemy.orm import exc as orm_exc

class DictConverter(AnyConverter):
    def __init__(self, map, **kws):
        items = kws.keys()
        self.kws = kws
        super(DictConverter,self).__init__(map, *items)
    def get_view_func(self):
        return self._view_func
    def set_view_func(self, view_func):
        from flaskext.submodule import Identifier
        mod = import_module(view_func.__module__)
        self.k2v = {k:(
            getattr(mod,v)
                       if isinstance(v, Identifier)
                       else v) for k,v in  self.kws.items()}
        self.v2k = dict((v, k) for k,v in self.k2v.items())
        self._view_func = view_func

    view_func = property(get_view_func, set_view_func)
    def to_url(self, value):
        return url_quote(self.v2k.get(value, value), self.map.charset)

    def to_python(self, value):
        return self.k2v[value]
    


class EmptiablePath(PathConverter):
    regex = r'(?:|[^/].*?)'#'[^/].*?'
    def to_url(self, value):
        
        return value
    
from flask.globals import current_app
current_app.url_map.converters['emptiable_path'] = EmptiablePath
current_app.url_map.converters['dict'] = DictConverter

from datetime import timedelta
from myojin.hashutils import urlsafe_hmac_digest, verify_urlsafe_hmac_digest

from werkzeug.routing import Rule, Map, BaseConverter, ValidationError
class BaseModelConverter(BaseConverter):
    HMAC_KEY = None
    def __init__(self, url_map, attr="encoded_id", tokenkind=None, minutes=30, days=0, uselist=False,
                 value_only=False, query_with=None):
        assert self.HMAC_KEY
        self.query_arg_name = query_with or self.model.default_query_arg4converter
        self.value_only = value_only
        self.tokenkind = tokenkind
        self.timedelta = timedelta(minutes=minutes, days=days)
        self.uselist = uselist
        assert not self.uselist or (self.tokenkind and attr=="encoded_id")
        regex=None
        if attr=="id":
            regex = regex or r'\d+'
        else:
            regex = regex or r'.+'
        super(BaseModelConverter, self).__init__(url_map)
        self.regex = regex
        self.attr = attr
    def decode_value(self, value):
        if self.uselist:
            value = value.encode("utf-8")
            val = [self.model.decode_id(value[i:i + 12]) for i in range(0, len(value), 12)]
            attr = 'id'
            query = getattr(self.model,self.query_arg_name)
            return query.filter(self.model.id.in_(val)).all()

        elif self.attr == "encoded_id":
            attr, val = ("id", self.model.decode_id(value.encode("utf-8")))
        else:
            attr, val = (self.attr, value)
        if val is None:
            raise ValidationError()
        if self.value_only:
            return val
        try:
            obj = getattr(self.model,self.query_arg_name).filter_by(**{attr:val}).one()
        except orm_exc.NoResultFound, e:
            raise ValidationError()
        except orm_exc.MultipleResultsFound, e:
            raise ValidationError()
        return obj
    def to_python(self, value):
        if self.tokenkind:
            attr_value = value[:-55]
            dt_digest = value[-55:]
            msg = attr_value + self.tokenkind
            key = self.HMAC_KEY
            from datetime import timedelta
            if not verify_urlsafe_hmac_digest(dt_digest, key, msg, self.timedelta):
                raise ValidationError()
            value = attr_value
        return self.decode_value(value)

    def to_url(self, value):
        if self.tokenkind:
            if self.uselist:
                attr_value = "".join(getattr(x, self.attr) for x in value)
            else:
                attr_value = getattr(value, self.attr)
            key = self.HMAC_KEY
            msg = attr_value + self.tokenkind
            print attr_value, urlsafe_hmac_digest(key=key, msg=msg)
            return attr_value + urlsafe_hmac_digest(key=key, msg=msg)
        import werkzeug.local
        assert isinstance(value, (self.model, werkzeug.local.LocalProxy, list, tuple))
        return str(getattr(value, self.attr))
