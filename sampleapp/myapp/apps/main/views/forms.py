# coding: utf-8

from flask_wtf import Form
from wtforms import TextField, TextAreaField, PasswordField, FileField, BooleanField, SelectField, RadioField, HiddenField
from wtforms.ext.sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField

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
                print '-----'
                print valuelist[0]
                self.data = json.loads(valuelist[0])
                print self.data
                #self.data = int(valuelist[0])
            except ValueError:
                raise ValueError(self.gettext(u'Not a valid integer value'))

class JqSearchField(JqBooleanField):
    name = property(
        lambda self:"_search",
        lambda self, value:p(value) or None
        )

class JqGridForm(Form):
    search = JqSearchField('')
    page = IntegerField('')
    rows = IntegerField('')
    page = IntegerField('')
    sidx = TextField('')
    sord = TextField('')
    filters = JsonField('')

