# encoding: utf-8
from __future__ import absolute_import
import rumalchemy
from rumalchemy import SARepository
from rum import RumApp
from tw.core.resources import _JavascriptFileIter
@classmethod
def escape(cls, s):
    """
    Replace everything with an underscore that
    could cause trouble.
    """
    return s.encode('utf8').translate(cls.TRANSLATION_TABLE)
_JavascriptFileIter.escape = escape
from flask import current_app
import gettext,os,inspect
#from webob import Request
import webob
class Request(webob.Request):
    def copy_body(self):
        pass
from subprocess import call
import os
from os.path import getctime

def get_po_ctime():
    return getctime(get_filename('po'))

def call_msgfmt():
    return call(['msgfmt',get_filename('po'),'-o',get_filename('mo')])

def get_filename(ext='po'):
    dirs = (current_app.root_path, current_app.config.get('I18N_DIR_NAME', 'locales'), 'ja', 'LC_MESSAGES')
    f = '%s.%s'% (current_app.import_name,ext)
    return os.path.join(*dirs + (f,))


def rum_response(rumpath,models):
    #regist_ms932_controllers(models)
    from flask.globals import request,current_app
    req = Request(request.environ)
    req = req.copy()
    req.path_info_pop()
    environ = req.environ
    if len(rumpath) == 0:
        environ['SCRIPT_NAME'] = request.environ['PATH_INFO']
    else:
        environ['SCRIPT_NAME'] = request.environ['PATH_INFO'][:-(len(rumpath)+1)]

    environ['PATH_INFO'] = "/"+rumpath
    info = dict()
    def s_r(status,headers,exc_info=None):
        info.update(status=status,headers=headers,exc_info=exc_info)
    rum_app = get_rum_app(models, str(current_app.db.engine.url), get_translator_from_app)
    response = rum_app(environ, s_r)
    return current_app.response_class(
        response=response,
        status=info['status'],
        #mimetype=mimetype,
        headers=info['headers'],
        direct_passthrough=True
        )


def get_translator_from_app():
    from flask.globals import current_app
    app = current_app
    domain = app.import_name
    return gettext.translation(
            domain=domain,
            languages=['ja'],
            localedir=os.path.join(app.root_path, app.config.get('I18N_DIR_NAME', 'locales')),
            fallback=True
            )
        

def create(self, data):
    argspec = inspect.getargspec(self.resource.__init__)
    if argspec.keywords:
        obj = self.resource(**data)
    else:
        obj = self.resource(**{k:data[k] for k in argspec.args if k in data})
    if obj in self.session:
        self.session.expunge(obj)
    if self.parent_obj is not None:
       self.attach_to_parent(obj)
    return obj

SARepository.create = create

class Translator(object):
    active_locale = "ja"
    def __init__(self, get_translator):
        self._get_translator = get_translator
        call_msgfmt()
        self._trans = get_translator()
        self.po_ctime = get_po_ctime()
    @property
    def trans(self):
##         if current_app.config.get('RUM_DEBUG',False) and current_app.config.get('DEBUG',False):
##             if self.po_ctime != get_po_ctime():
##                 self.po_ctime = get_po_ctime()
##                 #import sys;sys.exit()
##                 reload(gettext)
        return self._trans
    def ugettext(self, t):
        result = self.trans.ugettext(t)
        if result == t and current_app.config.get('RUM_DEBUG',False) and current_app.config.get('DEBUG',False):
            current_app.logger.debug('msgid: %s' % t)
        return result
    def ungettext(self, t):
        return self.trans.ungettext(t)

class CustomRumApp(RumApp):
    def __init__(self, *args,**kws):
        self.translator = Translator(kws.pop('translator'))
        super(CustomRumApp,self).__init__(*args,**kws)
        
from threading import Lock
_rum_app_lock = Lock()
_rum_app = None
def get_rum_app(models, url, get_translator, debug=False):
    global _rum_app
    if not _rum_app:
        with _rum_app_lock:
            if not _rum_app:
                _rum_app = load_app(models, url, get_translator, debug)
    return _rum_app

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
def load_app(models, url, translator, debug=False):
    
    app = CustomRumApp({
        'debug': debug,
        'templating': {'search_path': [BASE_DIR + '/templates/rum']},
        'rum.translator':{current_app.config.get('I18N_DIR_NAME', 'locales'):["es"],},
        'rum.repositoryfactory': {
            'use': 'sqlalchemy',
            'models': models,
            'sqlalchemy.url': url,
        },
        'rum.viewfactory': {
            'use': 'toscawidgets',
        }
    },finalize=True, translator=translator)
    
    return app

#import csv
#from cStringIO import StringIO
#from rum import app, fields
#from rum.controller import CRUDController, ControllerFactory
#process_output = CRUDController.process_output.im_func
#class Ms932CsvController(CRUDController):
#    @process_output.when(
#        "isinstance(output,dict) and 'items' in output and self.get_format(routes) in ['xls', 'csv', 'pdf']"
#    )
#    def _process_dict_as_csv(self, output, routes):
#        format=self.get_format(routes)
#        if 'csv' != format:
#            CRUDController._process_dict_as_csv(self, output, routes)
#        else:
#            output=output['items']
#            resource = routes['resource']
#            action=routes['action']
#            fields_for_resource=self.app.fields_for_resource(resource)
#            if fields_for_resource:
#                csv_fields=[f for f in fields_for_resource if not
#                    (isinstance(f, fields.Binary) or
#                        isinstance(f, fields.Collection))]
#                csv_fields=[f for f in csv_fields if
#                    app.policy.has_permission(obj=resource, attr=f.name, action=action)]
#            else:
#                #testing purposes
#                csv_fields=[]
#            self.response.body = self.to_csv(output, csv_fields)
#    def to_csv(self, items, fields):
#        def to_ms932(s):
#            if not isinstance(s, str):
#                s=u'' if s is None else unicode(s)
#                s=s.encode("ms932", 'replace')
#            return s
#        stream=StringIO()
#        writer=csv.writer(stream, dialect='excel')
#        writer.writerow([to_ms932(unicode(f.label)) for f in fields])
#        for i in items:
#            writer.writerow([to_ms932(getattr(i, f.name)) for f in fields])
#        value=stream.getvalue()
#        stream.close()
#        return value
#def regist_ms932_controllers(models):
#    for model in models:
#        ControllerFactory.register(Ms932CsvController, model)
