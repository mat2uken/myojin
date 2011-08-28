from functools import wraps
from flask import request, make_response, Response, jsonify
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
        self.ssl_required_endpoints = []
    def add_state(self, state):
        self._state = state

    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        super(Module,self).add_url_rule( rule, endpoint, view_func, **options)
        def setattr_view_func_to_conv(state):
            if '%s.%s' % (self.name, endpoint) != state.app.url_map._rules[-1].endpoint:
                return
            #assert '%s.%s' % (self.name, endpoint) == state.app.url_map._rules[-1].endpoint
            for c in state.app.url_map._rules[-1]._converters.values():
                c.view_func = view_func

        self._record(setattr_view_func_to_conv)
        
        @self._record
        def append_ssl_required_endpoints(state):
            state.app.ssl_required_endpoints.update(
                '%s.%s' % (self.name, endpoint)
                for endpoint in self.ssl_required_endpoints)

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
            if isinstance(v, (str, int, float,)):
                m[k] = v
            else:
                m.setlist(k,v)
    return m

def request_xhr(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.is_xhr:
            return f(*args, **kwargs)
        else: 
            return jsonify(result='ng', message='not allow to connect')
    return decorated

class SubModule(object):
    def __init__(self, import_name, name=None, url_prefix="", decorators=(),
                 default_route_args=None):
        if name is None:
            assert '.' in import_name, 'name required if package name ' \
                'does not point to a submodule'
            name = import_name.rsplit('.', 1)[1]
        self.default_route_args = default_route_args or dict()
        self.name = name
        self.urls = []
        self.ssl_required_endpoints = []
        self.url_prefix = url_prefix
        self.decorators = decorators

    def jsonify(self, methods=None):
        def decorator(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                if methods is not None and isinstance(methods, (list, tuple)):
                    if request.method.upper() not in methods:
                        return f(*args, **kwargs)
                ret = f(*args, **kwargs) or (dict(), True,)
                from werkzeug import BaseResponse
                if isinstance(ret, BaseResponse):
                    return ret
                else:
                    if isinstance(ret, (tuple, list,)):
                        ret_dict, result = ret
                    else:
                        ret_dict, result = ret, True
                    ret_dict['result'] = 'ok' if result else 'ng'
                    return jsonify(**ret_dict)
            return decorated
        return decorator

    def route(self, rule, decorators=(), argform=None, ssl_required=False, debug_only=False, xhr_required=False, **options):
        options = dict(self.default_route_args, **options)
        def decorator(f):
            if debug_only:
                from flask import current_app
                if not current_app.config.get('DEBUG', False):
                    return f
            decos = tuple(self.decorators) + tuple(decorators)
            if xhr_required:
                decos = tuple([request_xhr]) + decos

            if argform:
                decos += (partial(argform_deco,argform), )
            f = reduce(lambda f,d:d(f),
                       reversed(decos),
                       #decos,
                       f)
            endpoint = self.name + "." + f.__name__
            self.urls.append(dict(rule=self.url_prefix + rule,
                                  endpoint=endpoint,
                                  view_func=f,
                                  **options))
            if ssl_required:
                self.ssl_required_endpoints.append(endpoint)
            return f
        return decorator

    def redirect_to(self, condition, to, anchor=None):
        def decorator(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                if condition():
                    _anchor = anchor or f.__name__
                    from myojin.utils import redirect_to
                    return redirect_to(to, _anchor=_anchor)
                else:
                    return f(*args, **kwargs)
            return decorated
        return decorator

    def register_to(self, module):
        self.parent = module
        for url in self.urls:
            module.add_url_rule(**url)
        module.ssl_required_endpoints.extend(self.ssl_required_endpoints)

    def with_form(self, form):
        def decorator(f):
            @wraps(f)
            def decorated_func(*args, **kws):

                try:
                    if request.method == 'GET':
                        formdata = request.args
                    elif request.content_type.startswith("application/json"):
                        formdata = dict(data=request.stream.read())
                    else:
                        if request.content_type.startswith("application/json"):
                            formdata = dict(data=request.stream.read())
                        else:
                            formdata = request.form
                except IOError as e:
                    flask.abort(400)

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
                         **dict(kws, **dict(
                             (k,(getattr(info, k) if hasattr(v,"stream") else v))
                             for k,v in info.data.items() if
                             k != "csrf" and
                             (hasattr(v,"stream") or v)
                             )))
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
    from flask import current_app, request
    app = current_app
    environ = request.environ
##     if "logout" in endpoint:
##         print app.config['SERVER_NAME'], environ.get('HTTP_HOST'), environ.get('SERVER_NAME')
    if endpoint == ".":
        endpoint = request.endpoint
        if not _args:
            _args = request.args

    is_https = endpoint in current_app.ssl_required_endpoints
    if '_https' in values and values['_https'] == True:
        is_https = True
        del values['_https']
    if bool(is_https) != bool(current_app.is_ssl_request()) and endpoint != ".static":
        values['_external'] = True
    result = flask._url_for(endpoint, **values)

    # localhost -> app.config["HTTP_HOST"]
    result = result.replace('localhost', app.config["HTTP_HOST"])

    #print result, is_https, current_app.is_ssl_request()
    if is_https and (not current_app.config.get('DEBUG') or current_app.config.get('HTTP_USE_SSL')):
        if result.startswith('http://'):
            result = 'https://' + result[len('http://'):]
            items = result.split("/",3)
            items[2] = items[2].split(":")[0]
            result = "/".join(items)
    if current_app.is_ssl_request() and not is_https and result.startswith('http://'):
        items = result.split("/",3)
        port = current_app.config.get("EXT_HTTP_PORT") or current_app.config['HTTP_PORT']
        items[2] = items[2].split(":")[0] + (
            ":%s" % port if int(port) != 80 else "")
        result = "/".join(items)
        
        #result = result.replace('http://', 'https://')

    if hasattr(_args, "lists"):
        args = [(k,v) for k, vs in _args.lists for v in vs]
    else:
        args = _args

    if args:
        return "%s?%s" % (result, urlencode(args))
    else:
        return result
flask.url_for = url_for
