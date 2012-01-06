# coding: utf-8
from flaskext.wtf import QuerySelectMultipleField, QuerySelectField


class CustomQuerySelectMultipleField(QuerySelectMultipleField):
    def __init__(self, column=None, get_key=None, order_by=None, query_with=None, *args,**kws):
        super(CustomQuerySelectMultipleField,self).__init__(*args,**kws)
        query = self.query_factory()
        if hasattr(query,'_entities'):
            model = query._entities[0].type
        elif hasattr(query,'impl'): 
            model = query.impl.class_
        else:
            assert False

        if query_with is not None:
            self.query = getattr(model, query_with)
        else:
            self.query = query

        self.column = column or model.id
        self.get_key = get_key or model.decode_id
        self.order_by = order_by

    def _get_data(self):
        formdata = self._formdata
        if formdata is None:
            return self._data
        
        keys = [self.get_key(x) for x in self._formdata]
#        q = self.query_factory().filter(self.column.in_(keys))
        q = self.query.filter(self.column.in_(keys))
        if self.order_by is not None:
            q = q.order_by(self.order_by)
        data = q.all()
        if len(data) != len(formdata):
            self._invalid_formdata = True
        self._set_data(data)
        return data

    def _set_data(self, data):
        self._data = data
        self._formdata = None

    data = property(_get_data, _set_data)

    def iter_choices(self):
        for pk, obj in self._get_object_list():
            yield (pk, self.get_label(obj), obj in self.data)

    def process_formdata(self, valuelist):
        self._formdata = set(valuelist)

    def pre_validate(self, form):
        if self._invalid_formdata:
            raise ValidationError('Not a valid choice')
        elif self.data:
            return
            obj_list = list(x[1] for x in self._get_object_list())
            for v in self.data:
                if v not in obj_list:
                    raise ValidationError('Not a valid choice')

class CustomQuerySelectField(QuerySelectField):
    def __init__(self , column, **kws):
        super(CustomQuerySelectField,self).__init__( **kws)
        self.column = column

    def _get_data(self):
        if self._formdata is not None:
            query = self.query or self.query_factory()
            if isinstance(column, basestring):
                obj = query.filter_by(**{column: self._formdata}).first()
            else:
                obj = query.filter(column==self._formdata).first()
            self._set_data(obj)
        return self._data

from flaskext.wtf import Form, TextField, TextAreaField, QuerySelectField, QuerySelectMultipleField, PasswordField, FileField, BooleanField, SelectField, RadioField, HiddenField, SelectMultipleField, IntegerField

#def getrows(form=None, _search=False, rows=None, page=None, sidx=None, sord=None):
def coerce_bool(s):
    print "s:",s
    return True

def p(s):
    print "P:", s
class JqBooleanField(TextField):
    def process_formdata(self, valuelist):
        print "valuelist:", valuelist
        if valuelist:
            try:
                self.data = "true" == valuelist[0]
                #self.data = int(valuelist[0])
            except ValueError:
                raise ValueError(self.gettext(u'Not a valid integer value'))

class JsonField(TextField):
    def process_formdata(self, valuelist):
        if valuelist:
            try:
                import json
                self.data = json.loads(valuelist[0])
                #self.data = int(valuelist[0])
            except ValueError:
                raise ValueError(self.gettext(u'Not a valid integer value'))

class JqSearchField(JqBooleanField):
    name = property(
        lambda self:"_search",
        lambda self, value: None
        )



from wtforms.validators import ValidationError
class QueryTextField(TextField):
#raise ValidationError('Not a valid choice')
    def __init__(self, *args, **kws):
        to_obj  = kws.pop("to_obj", None)
        self.error_message  = kws.pop("error_message", None)
        TextField.__init__(self, *args, **kws)
        self.to_obj = to_obj
        
    def pre_validate(self, form):
        if self.data is None and getattr(self,"_formdata", None):
            raise ValidationError(self.error_message)
        
    def process_formdata(self, valuelist):
        self.allow_blank = True
        self._formdata = valuelist[0].strip() if valuelist else None
        if self._formdata is not None:

            self.data = self.to_obj(self._formdata)
    def _value(self):
        return getattr(self,"_formdata", None) or u""
