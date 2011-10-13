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

class JQGridEditForm(custom_wtf.Form):
    id = custom_wtf.IntegerField('')
    oper = custom_wtf.TextField('')

class JQGridField(object):
    def setattr(self, obj, value):
        setattr(obj, self.column_name,  self.to_python(value))
        #obj.account_status = self.to_python(value)
        #print "setattr", obj, repr(self.column_name),  repr(self.to_python(value))
        #import pdb;pdb.set_trace()

    def filter(self, model, query, data, **kws):
        return query.filter_by(**{
            self.column_names[0]:self.to_python(data)
            })
    def to_python(self, data):
        return data
    def __init__(self, column_names, disp_name=None, width=60, editable=False):
        self.disp_name = disp_name or column_names
        self.column_names = filter(None, column_names.split("."))
        self.width = width
        self.editable = editable
    @property
    def column_name(self):
        return self.column_names[0] if self.column_names else None
    edittype = "text"
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
            editable=self.editable,
            cellEdit=self.editable,
            edittype=self.edittype,
            editrules=dict(edithidden=True,),
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

class BooleanField(JQGridField):
    def to_python(self, data):
        return data.lower().strip() in ("true", "1")

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
from dateutil.relativedelta import relativedelta
        
class DatetimeField(JQGridField):
    default_col_model_args = dict(sortable=True,
                                  editable=False,
                                  search=True,)
    default_strftime = "%y/%m/%d %H:%M"
     
    def __init__(self,  *args, **kws):
        self.strftime = kws.pop('strftime', self.default_strftime)
        super(DatetimeField,self).__init__(*args, **kws)
        
    def to_col_data(self, x):
        return x.strftime(self.strftime) if x else ""
    ## def to_python(self, data):
    ##     return int_or(data)

    def filter(self, model, query, data, **kws):
        from datetime import datetime, date
        dt_str = data.strip().split("/")
        if dt_str[0]:
            year = int(dt_str[0]) + (2000 if len(dt_str[0]) == 2 else 0)
        else:
            year = date.today().year
        month = int(dt_str[1]) if len(dt_str) > 1 else None
        day = int(dt_str[2]) if len(dt_str) > 2 else None
        col= getattr(model, self.column_name)
        if year and month and day:
            return query.filter(col == datetime(year, month, day))
        elif year and month and not day:
            start_date = datetime(year, month, 1)
            end_date = datetime(year, month, 1) + relativedelta(months=1, day=1)
        elif year and not month and not day:
            start_date = datetime(year, 1, 1)
            end_date = datetime(year + 1, 1, 1)
        return query.filter(col >= start_date).filter(col < end_date)

class DateField(DatetimeField):
    default_strftime = "%y/%m/%d"

class ObjectField(JQGridField):
    @property
    def column_name(self):
        return self.column_names[0] + "_id"
    
    def filter(self, model, query, data, **kws):
        if ":" in data:
            id = int(data.split(":").strip())
        else:
            if int_or(data) is None:
                return self.query
            id = int_or(data)
        return query.filter_by(**{
            self.column_names[0]:self.target_query.get(id)
            })
    @property
    def target_query(self):
        return self.target_query_func()
    
    def __init__(self,  *args, **kws):
        self.target_query_func = kws.pop('target_query')
        self.stype = kws.pop('stype',None)
        super(ObjectField,self).__init__(*args, **kws)
        self.column_names, self.view_column_name = self.column_names[:-1], self.column_names[-1]

    def to_col_data(self, x):
        return getattr(x, self.view_column_name,"")
        return "%s(ID:%s)" % (getattr(x, self.view_column_name,""),x.id, )

    def get_col_model(self):
        add_op = dict()
        if self.stype == "select":
            add_op = dict(
                stype="select",
                searchoptions=
                dict(
                    value=":ALL;" + ";".join("%s:%s" % (x.id, getattr(x,self.view_column_name)) for x in self.target_query.all())
                    ))
            
        
        return dict(
            super(ObjectField, self).get_col_model(),
            name=str(self.index),
            index=str(self.index),
            width=self.width,
            **add_op
            )

class SelectField(IntegerField):
        
    def to_python(self, data):
        return self.to_python_func(data)
    
    def __init__(self,  *args, **kws):
        self.options = kws.pop('options')
        if isinstance(self.options[1][0], int):
            self.to_python_func = kws.pop('to_python', int_or)
        else:
            self.to_python_func = kws.pop('to_python', lambda x:x)
        self.to_col_data_dict = dict(self.options)
        self.stype = "select"
        super(SelectField,self).__init__(*args, **kws)
    edittype = "select"

    def to_col_data(self, x):
        return self.to_col_data_dict.get(x,None)

##         return "%s(ID:%s)" % (getattr(x, self.view_column_name,""),x.id, )

    def get_col_model(self):
        value = ";".join("%s:%s" % (value, name) for value, name in self.options)
        add_op = dict(
            stype="select",
            editoptions=dict(value=value),
            searchoptions=dict(value=":ALL;" + value))
        return dict(
            super(SelectField, self).get_col_model(),
            name=str(self.index),
            index=str(self.index),
            width=self.width,
            **add_op
            )

from collections import OrderedDict

class JQGrid(object):
    def edit_row(self, id, form):
        obj = self.query.get(id)
        result = [self.fields[int(k)].setattr(obj, v) for k,v in form.items() if int_or(k)]
        
        return dict()
    @property
    def query(self):
        return self.query_func()
    def __init__(self, model, query, fields):
        self.query_func = query
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
            colModel=self.get_col_model(),
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
        field_rules = [( self.fields[int(rule['field'])], rule) for rule in filters['rules']]
        return reduce(lambda q, (f, rule):f.filter(self.model, q, **rule), field_rules, query)

    def get_order(self, query, sidx, sord):
        try:
            field = self.fields[int(sidx)]
        except ValueError:
            return query
        col = getattr(self.model, field.column_name)
        from sqlalchemy import desc, asc
        return query.order_by(dict(desc=desc).get(sord, asc)(col))

    def get_data(self, query=None, search=False, rows=None, page=None, sidx=None, sord=None,filters=None):
        filtered_query = self.get_order(self.get_query(
            query or self.query, filters), sidx, sord)
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
