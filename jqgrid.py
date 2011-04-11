# coding:utf-8
from myojin.funcutils import getattrs

#from myojin.custom_wtf import JqSearchField, IntegerField, TextField, JsonField, Form
from myojin import custom_wtf
class JQGridIndexForm(custom_wtf.Form):
    search = custom_wtf.JqSearchField('')
    page = custom_wtf.IntegerField('')
    rows = custom_wtf.IntegerField('')
    sidx = custom_wtf.TextField('')
    sord = custom_wtf.TextField('')
    filters = custom_wtf.JsonField('')

class JQGridField(object):

    def filter(self, query, data, **kws):
        return query.filter_by(**{
            self.column_names[0]:self.to_python(data)
            })
    def to_python(self, data):
        return data
    def __init__(self, column_names, disp_name, width=60):
        self.column_names = filter(None, column_names.split("."))
        self.disp_name=disp_name
        self.width = width
    @property
    def column_name(self):
        return self.column_names[0] if self.column_names else None
        
    default_col_model_args = dict(
        sortable=True,
        editable=False,
        search=True,
        )
    def get_col_model(self):
        return dict(
            self.default_col_model_args,
            name=str(self.index),
            index=str(self.index),
            width=self.width,
            )
    def to_col_data(self, x):
        return x
    def get_col_data(self, obj):
        value = getattrs(obj, self.column_names)
        if hasattr(value, "__iter__"):
            return ", ".join(self.to_col_data(x) for x in value)
        return self.to_col_data(value)
def int_or(n):
    try:
        return int(n)
    except:
        return None

class IntegerField(JQGridField):
    def to_python(self, data):
        return int_or(data)

class LinkField(JQGridField):
    def __init__(self,  *args, **kws):
        self.href_func = kws.pop('href')
        self.label_func = kws.pop('label')
        super(LinkField,self).__init__(*args, **kws)

    def to_col_data(self, x):
        return '<a href="%s">%s</a>' % (self.href_func(x), self.label_func(x))
    default_col_model_args = dict(
        sortable=False,
        editable=False,
        search=False,
        )
        
class DatetimeField(JQGridField):
    default_col_model_args = dict(sortable=True,
                                  editable=False,
                                  search=False,)
    def to_col_data(self, x):
        return x.strftime("%y/%m/%d %H:%M") if x else ""
    
class ObjectField(JQGridField):
    @property
    def column_name(self):
        return self.column_names[0] + "_id"
    
    def filter(self, query, data, **kws):
        if ":" in data:
            id = int(data.split(":").strip())
        else:
            if int_or(data) is None:
                return self.query
            id = int_or(data)
        return query.filter_by(**{
            self.column_names[0]:self.target_query.get(id)
            })
    
    def __init__(self,  *args, **kws):
        self.target_query = kws.pop('target_query')
        super(ObjectField,self).__init__(*args, **kws)
        self.column_names, self.view_column_name = self.column_names[:-1], self.column_names[-1]

    def to_col_data(self, x):
        print x, self.view_column_name
        return "%s(ID:%s)" % (getattr(x, self.view_column_name,""),x.id, )

    def get_col_model(self):
        
        return dict(
            self.default_col_model_args,
            name=str(self.index),
            index=str(self.index),
            width=self.width,
            stype="select",
            #dataUrl="ABC",
             searchoptions=
             dict(
                value=":ALL;" + ";".join("%s:%s" % (x.id, getattr(x,self.view_column_name)) for x in self.target_query.all())
                )
##                 value=OrderedDict([
##                     ("","ALL"),
##                     ("1",u"デフォルト"),
##                     ("2",u"トライアル"),
##                     ("3",u"スタンダード"),
##                     ])
##                 )
            )
from collections import OrderedDict

class JQGridForm(object):
    def __init__(self, model, query, fields):
        self.query = query
        self.fields = fields
        self.model = model
        for i, x in enumerate(self.fields):
            x.index = i
    def get_col_names(self):
        return [
            x.disp_name
            for x in self.fields]
    def get_col_model(self):
        return [
            x.get_col_model()
            for i, x in enumerate(self.fields)]
    def get_init_data(self):
        return dict(
            colNames=self.get_col_names(),
            colModel=self.get_col_model()
            )
    def get_json_data(self, *args, **kws):
        import json
        return json.dumps(self.get_data(*args,**kws))

    def get_cols(self, obj):
        return [
            field.get_col_data(obj)
            for field in self.fields
            ]
    def get_query(self, query, filters):
        if not filters:
            return query
##         {u'groupOp': u'AND',
##          u'rules': [{u'data': u'aaa', u'field': u'nickname', u'op': u'bw'},
##                     {u'data': u'123', u'field': u'user_type', u'op': u'bw'}]}
        pprint(filters['rules'])
        field_rules = [( self.fields[int(rule['field'])], rule) for rule in filters['rules']]
        return reduce(lambda q, (f, rule):f.filter(q, **rule), field_rules, query)

    def get_order(self, query, sidx, sord):
        try:
            field = self.fields[int(sidx)]
        except ValueError:
            return query
        col = getattr(self.model, field.column_name)
        print "col:",col
        from sqlalchemy import desc, asc
        return query.order_by(dict(desc=desc).get(sord, asc)(col))
        #return query
    def get_data(self, query=None, search=False, rows=None, page=None, sidx=None, sord=None,filters=None):
        filtered_query = self.get_order(self.get_query(
            query or self.query, filters), sidx, sord)
        print "page:", repr(page),type(page)
        start = (page - 1) * rows
        end = start + rows
        rows_data = [
            dict(id=x.id, cell=self.get_cols(x))
            for x in 
            filtered_query[start:end]]
        total = int(math.ceil(filtered_query.count() / float(rows)))
        data = dict(
            page=page,
            total=total,
            rows=rows_data,
            records=len(rows_data))
        return data
        
import math
from pprint import pprint
