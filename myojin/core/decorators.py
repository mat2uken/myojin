from .globals import current_user
from functools import wraps
from flask import request, session, url_for, redirect

def login_required(redirect_to=lambda *args, **kws:url_for("main.top.login", \
                   next='/%s%s' % (request.script_root, request.url.replace(request.url_root, ''))),
                   is_authenticated=lambda *args,**kws:current_user.is_authenticated()):
    def decorator(f):
        @wraps(f)
        def decorated(*args,**kws):
            #import time;time.sleep(10)
            if not is_authenticated(*args,**kws):
                return redirect(redirect_to(*args,**kws))
            return f(*args,**kws)
        return decorated
    return decorator
    
from werkzeug.exceptions import NotFound
def admin_required():
    def decorator(f):
        @wraps(f)
        def decorated(*args,**kws):
            if current_user.is_authenticated() and current_user.is_admin:
                return f(*args,**kws)
            return redirect(url_for('main.top.adminlogin'))
        return decorated
    return decorator

def post_session_id():
    def decorator(f):
        @wraps(f)
        def decorated(*args,**kws):
            from flask.globals import _request_ctx_stack, request, current_app
            sid = request.form.get('sid', request.args.get('sid', None))
            if sid:
                Session = type(_request_ctx_stack.top.session)
                arg_session = Session(dict(), id=sid, **current_app.session_middleware.options)
                arg_session.load()
                session._form_session = arg_session
            return f(*args,**kws)
        return decorated
    return decorator

from IPy import IP
def admin_ip_check():
    def decorator(f):
        @wraps(f)
        def decorated(*args,**kws):
            from .globals import allow_ip_address, reset_allow_ip_address
            ip_address = allow_ip_address
            if allow_ip_address is None:
                from myojin.models import AllowIPAddress
                allow = AllowIPAddress.query.first()
                ip_address = [] if allow is None else allow.ip_address
                reset_allow_ip_address(ip_address)

            ip_int_set = frozenset(
                ip.int()
                for iplist in ip_address
                for ip_range_str in ip_address
                for ip in IP(ip_range_str)
            )

            if IP(request.environ['REMOTE_ADDR']).int() in ip_int_set:
                return f(*args,**kws)
            from myojin import app
            app.logger.debug('ip fail!!')
            app.logger.debug(request.environ['REMOTE_ADDR'])
            app.logger.debug(allow_ip_address)
            raise NotFound()
        return decorated
    return decorator
