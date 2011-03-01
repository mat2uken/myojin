from flaskext.wtf import QuerySelectMultipleField

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
