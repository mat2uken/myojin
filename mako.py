# -*- coding: utf-8 -*-
from __future__ import absolute_import
from mako.lookup import TemplateLookup
_lookup = None
from flask import request, session

def init(app,globals=None):
    global _globals, _lookup
    
    _lookup = init_lookup(app.root_path + "/templates", app.root_path + "/tmp", globals=globals)
    _globals = globals or dict()
    _globals['DEBUG'] = app.config.get('DEBUG', False)
_globals = None

def get_template(template_name):
    tmpl = _lookup.get_template(template_name)
    return tmpl
    
def init_lookup(directory, module_directory, globals=None):
    return TemplateLookup(directories=[directory], module_directory=module_directory,
                          input_encoding="utf-8",
                          output_encoding="utf-8",
                          #imports=["from json import dumps as JSON"],
                          default_filters=['h'])
    
##     global _lookup
##     global _globals
##     _globals = globals or dict()
##     _lookup = TemplateLookup(directories=[directory], module_directory=module_directory,input_encoding="utf-8")

def render(template_name, ctx,to_unicode=False):#, *args, **kws):
    tmpl = get_template(template_name)
##     from flask import _request_ctx_stack
##     app = _request_ctx_stack.top.app
##     lookup2 = init_lookup(app.root_path + "/templates", app.root_path + "/tmp", globals=globals)
    
    # TODO: cache tmpl
    render = tmpl.render if to_unicode else tmpl.render_unicode
    return render(request=request,session=session, **dict(
        mako_utils.items() +
        _globals.items() + ctx.items()))
from mako.filters import html_escape
from markupsafe import escape, Markup
def newline_filter(s):
    #assert isinstance(s, basestring)
    #assert isinstance(s, unicode)
    if isinstance(s, str):
        s = unicode(s)
    elif isinstance(s, unicode):
        pass
    else:
        assert False
    return Markup(unicode(s).replace(u'\n',u'<br/>\n'))
##     return escape(s).replace('\n','<BR/>\n')
##     return Markup(escape(s).replace('\n','<br/>\n'))
##     return "<h1>HELLO</h1>"+html_escape(s).replace('\n','<br/>\n')

from json import dumps
def json_dumps(s):
    assert isinstance(s, (list,dict))
    return Markup(dumps(s))
    #dumps
def debug_space(s):
    assert isinstance(s, unicode)
    return unicode(s).replace(u' ',u'　')
try:
    from flaskext.babel import gettext # as _
except ImportError, e:
    def gettext(*args, **kws):
        from flaskext.babel import gettext

mako_utils = dict(_=gettext, newline=newline_filter, debug_space=debug_space,JSON=json_dumps)
