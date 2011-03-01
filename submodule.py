from functools import wraps
from flask import request, make_response, Response
from myojin.auth import UserModelBase

class Identifier(str):
    def __getattr__(self, name):
        v = Identifier(name)
        setattr(self, name, v)
        return v

def get_converter(map, name, args):
    """Create a new converter for the given arguments or raise
    exception if the converter does not exist.

    :internal:
    """
    if not name in map.converters:
        raise LookupError('the converter %r does not exist' % name)
    if args:
        storage = type('_Storage', (), {'__getitem__': lambda s, x: Identifier(x)})()
        args, kwargs = eval(u'(lambda *a, **kw: (a, kw))(%s)' % args, {}, storage)
    else:
        args = ()
        kwargs = {}
    return map.converters[name](map, *args, **kwargs)
from werkzeug import routing
routing.get_converter = get_converter

import flask
class Module(flask.Module):
    def __init__(self, *args,**kws):
        super(Module, self).__init__(*args,**kws)
        self._record(self.add_state)
        
    def add_state(self, state):
        self._state = state

    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        super(Module,self).add_url_rule( rule, endpoint, view_func, **options)
        def setattr_view_func_to_conv(state):
            assert '%s.%s' % (self.name, endpoint) == state.app.url_map._rules[-1].endpoint
            for c in state.app.url_map._rules[-1]._converters.values():
                c.view_func = view_func

        self._record(setattr_view_func_to_conv)


from functools import wraps
def argform_deco(argform, f):
    from flask import request
    @wraps(f)
    def decorated(*args, **kws):
        form = argform(request.args)
        from flask import current_app
        if not form.validate():
            flask.abort(400)
##         current_app.debug_out.pprint(form.data)
        return f(*args, **dict(kws,**form.data))
    return decorated

from functools import partial
import json
from werkzeug import MultiDict

def json2multidict(jsonstr):
    jsondata = json.loads(jsonstr)
    m = MultiDict()
    for k,v in jsondata.items():
        if v is not None:
            m.setlist(k,v)
    return m

    #aaa
class SubModule(object):
    def __init__(self, import_name, name=None, url_prefix="", decorators=()):
        if name is None:
            assert '.' in import_name, 'name required if package name ' \
                'does not point to a submodule'
            name = import_name.rsplit('.', 1)[1]
        self.name = name
        self.urls = []
        self.url_prefix = url_prefix
        self.decorators = decorators
    def route(self, rule, decorators=(), argform=None, **options):
        def decorator(f):
            decos = tuple(self.decorators) + tuple(decorators)
            if argform:
                decos += (partial(argform_deco,argform), )
            f = reduce(lambda f,d:d(f),
                       decos,
                       f)
            self.urls.append(dict(rule=self.url_prefix + rule,
                                  endpoint=self.name + "." + f.__name__,
                                  view_func=f,
                                  **options))
            return f
        return decorator
    
    def register_to(self, module):
        self.parent = module
        for url in self.urls:
            module.add_url_rule(**url)

    def with_form(self, form):
        def decorator(f):
            @wraps(f)
            def decorated_func(*args, **kws):

                if request.method == 'GET':
                    formdata = request.args
                elif request.content_type.startswith("application/json"):
                    formdata = dict(data=request.stream.read())
                else:
                    if request.content_type.startswith("application/json"):
                        formdata = dict(data=request.stream.read())
                    else:
                        formdata = request.form
                if "data" in formdata:
                    formdata = json2multidict(formdata['data'])
                info = form(formdata, csrf_enabled=False)

##                 if not info.is_submitted():
##                     return f(form=info, *args,**kws)
##                 if not info.validate():
##                     flask.abort(400)
##                for k,v in info.data.items():
##                    print 'form:',k,v
                return f(form=info, *args,
                         **dict(kws, **{
                             k:(getattr(info, k) if hasattr(v,"stream") else v)
                             for k,v in info.data.items() if
                             k != "csrf" and
                             (hasattr(v,"stream") or v)
                             }))
            return decorated_func
        return decorator

    def templated(self, template=None, with_functions=[], with_cookies=[]):
        def decorator(f):
            @wraps(f)
            def decorated_func(*args, **kws):
                ctx = f(*args, **kws)
                if isinstance(ctx,dict) and ctx.get("template"):
                    template_name = ctx['template']
                elif isinstance(ctx, Response):
                    self.set_cookies(ctx, with_cookies)
                    return ctx
                else:
                    template_name = template
                html_string = render_template(template_name, ctx, with_functions)
                response = make_response(html_string)
                self.set_cookies(response, with_cookies)
                return response
            return decorated_func
        return decorator

    def set_cookies(self, response, with_cookies):
        for _cookie in with_cookies:
            cookie = _cookie() if type(_cookie) == type(lambda: hoge) else _cookie
            response.set_cookie(cookie.pop('key'), cookie.pop('value'), **cookie)

    def user_agent(self, bind_name=None):
        def decorator(f):
            @wraps(f)
            def decorated_func(*args, **kws):
                ctx = f(*args, **kws)
                ctx[bind_name if bind_name is not None else 'useragent'] = request.headers['user-agent']
                return ctx
            return decorated_func
        return decorator


def render_template(template_name, ctx, with_functions):
    from myojin.mako import render
    if template_name is None:
        template_name = request.endpoint.replace(".","/")+".html"
    elif template_name.startswith("/"):
        template_name = template_name[1:]
    else:
        template_name = "/".join(request.endpoint.split(".")[:-1] + [template_name])
    if ctx is None:
        ctx = {}
    elif not isinstance(ctx, dict):
        return ctx
    else:
        for fn in with_functions:
            ctx.update(fn())
    if not isinstance(ctx,dict):
        return ctx
    return render(template_name, ctx)
    
import flask
flask._url_for = flask.url_for
from flask import request
from urllib import urlencode
def url_for(endpoint, _args=(), **values):
    if endpoint == ".":
        endpoint = request.endpoint
        if not _args:
            _args = request.args

    is_https = False
    from flask import current_app
    if '_https' in values and values['_https'] == True:
        is_https = True
        del values['_https']

    result = flask._url_for(endpoint, **values)
    if is_https and not current_app.config.get('DEBUG'):
        result = result.replace('http://', 'https://')

    if hasattr(_args, "lists"):
        args = [(k,v) for k, vs in _args.lists for v in vs]
    else:
        args = _args

    if args:
        return "%s?%s" % (result, urlencode(args))
    else:
        return result
flask.url_for = url_for