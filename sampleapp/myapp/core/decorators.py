from .globals import current_user, current_app
from functools import wraps
from flask import request, url_for, redirect, jsonify

def login_required(redirect_to=lambda *args, **kws:url_for("main.top.login", \
                   next='/%s%s' % (request.script_root, request.url.replace(request.url_root, ''))),
                   is_authenticated=lambda *args,**kws:current_user.is_authenticated()):
    def decorator(f):
        @wraps(f)
        def decorated(*args,**kws):
            if not is_authenticated(*args,**kws):
                current_app.logger.debug('not logged-in user: user=>%s, path=>%s' % (current_user, request.path))
                if request.is_xhr:
                    return jsonify(result='ok', __location__=url_for('main.top.login'))
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
                current_app.logger.debug('logged-in by admin user: user=>%s, path=>%s' % (current_user, request.path))
                return f(*args,**kws)
            else:
                current_app.logger.debug('logged-in by non-admin user or not logged-in: user=>%s, path=>%s' % (current_user, request.path))
                return redirect(url_for('admin.top.login'))
        return decorated
    return decorator
