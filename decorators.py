from functools import wraps
from flask import _request_ctx_stack, request

def commit_on_success(*methods):
    methods = tuple(x.lower() for x in methods)
    for x in methods:
        assert x in ('get','post','put','delete')
    def decorator(f):
        @wraps(f)
        def decorated_func(*args, **kws):
            if methods and request.method.lower() not in methods:
                return f(*args, **kws)
            app = _request_ctx_stack.top.app
            session = app.db.session
            try:
                result = f(*args, **kws)
            except:
                app.logger.debug('!' * 100)
                app.logger.debug('commit_on_success: exception occured, path=%s' % (request.path))
                app.logger.debug('!' * 100)
                session.rollback()
                session.remove()
                raise
            else:
                try:
                    if result is not None and hasattr(result, 'is_not_commit') is True:
                        pass
                    else:
                        app.logger.debug('+' * 100)
                        app.logger.debug('commit_on_sucess: commit start')

                        session.commit()

                        app.logger.debug('+' * 100)
                        app.logger.debug('commit_on_success: commit done')

                        if app.config.get('SQLALCHEMY_RECORD_QUERIES', False):
                            from flaskext.sqlalchemy import get_debug_queries
                            queries = get_debug_queries()
                            if len(queries) > 0:
                                app.logger.debug('+' * 100)
                                for query in get_debug_queries():
                                    if query.duration >= 3:
                                        app.logger.debug(
                                            'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                                            % (query.statement, query.parameters, query.duration, query.context))
                                app.logger.debug('+' * 100)
                except:
                    app.logger.debug('=' * 100)
                    app.logger.debug('commit_on_success: commit failed')
                    session.rollback()
                    session.remove()
                    app.logger.debug('commit_on_success: session removed on commit failed')
                    app.logger.debug('=' * 100)
                    raise
            session.remove()
            return result
        return decorated_func
    return decorator

from werkzeug.exceptions import HTTPException, NotFound
def ip_restriction(*iplists):
    from IPy import IP
    ip_int_set = frozenset(
        ip.int()
        for iplist in iplists
        for ip_range_str in ([iplist] if isinstance(iplist,basestring) else iplist)
        for ip in IP(ip_range_str))
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kws):
            try:
                ip_int = IP(request.environ['REMOTE_ADDR']).int()
            except:
                raise NotFound()
            if ip_int in ip_int_set:
                print ip_int_set
                return f(*args, **kws)
            raise NotFound()
        return decorated
    return decorator
     
