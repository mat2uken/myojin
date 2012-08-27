# -*- coding: utf-8 -*-
from __future__ import absolute_import
from mako.lookup import TemplateLookup
_lookup = None
from flask import request, session, url_for
from myojin import custom_script

def init(app,globals=None):
    global _globals, _lookup
    
    _lookup = init_lookup(app.root_path + "/templates", app.root_path + "/tmp", globals=globals)
    _globals = globals or dict()
    _globals['DEBUG'] = app.config.get('DEBUG', False)
    _globals['url_for'] = url_for

    import os
    from flask import request
    production_config = custom_script.read_pyconfig(app, 'production.cfg')
    static_url_path = app.config.get('STATIC_URL_PATH', '/static')
    static_url_path_prod = production_config.get('STATIC_URL_PATH')
    def static(p):
        if request.args.get('production') == '1':
            ap = os.path.join(static_url_path_prod, p)
        else:
            ap = os.path.join(static_url_path, p)
        return ap.replace('http', 'https') if request.is_secure else ap.replace('https', 'http')
    _globals['static'] = static
    _globals['static_url'] = static_url_path
    static_misc_url_path = app.config.get('STATIC_MISC_URL_PATH', '/static')
    static_misc_url_path_prod = production_config.get('STATIC_MISC_URL_PATH')
    def static_for_misc(p):
        if request.args.get('production') == '1':
            ap = os.path.join(static_misc_url_path_prod, p)
        else:
            ap = os.path.join(static_misc_url_path, p)
        return ap.replace('http', 'https') if request.is_secure else ap.replace('https', 'http')
    _globals['static_for_misc'] = static_for_misc
_globals = None

def get_template(template_name):
    tmpl = _lookup.get_template(template_name)
    return tmpl
    
def init_lookup(directory, module_directory, globals=None):
    return TemplateLookup(directories=[directory], module_directory=module_directory,
                          input_encoding="utf-8",
                          output_encoding="utf-8",
                          default_filters=['h'])
    
def render(template_name, ctx=dict(), to_unicode=False):#, *args, **kws):
    tmpl = get_template(template_name)
    
    # TODO: cache tmpl
    render = tmpl.render if to_unicode else tmpl.render_unicode
    return render(request=request,session=session, **dict(
        mako_utils.items() +
        _globals.items() + ctx.items()))

from mako.filters import html_escape
from markupsafe import escape, Markup
def newline_filter(s, escape=False):
    if isinstance(s, str):
        s = unicode(s)
    elif isinstance(s, unicode):
        pass
    else:   
        assert False
    if escape:
        s = cgi.escape(s, True)
    return Markup(unicode(s).replace(u'\n',u'<br/>\n'))

from json import dumps
def json_dumps(s):
    assert isinstance(s, (tuple,list,dict))
    return Markup(dumps(s))

def debug_space(s):
    assert isinstance(s, unicode)
    return unicode(s).replace(u' ',u'　')

try:
    from flaskext.babel import gettext # as _
except ImportError, e:
    def gettext(*args, **kws):
        from flaskext.babel import gettext

def comma_num_filter(n):
    if isinstance(n, basestring):
        n = int(n)
    return "{:,d}".format(n)

def get_locale():
    try:
        from flaskext import babel
        return babel.get_locale()
    except:
        return None

mako_utils = dict(
    _=gettext,
    newline=newline_filter,
    debug_space=debug_space,
    JSON=json_dumps,
    comma=comma_num_filter,
    get_locale=get_locale
)
