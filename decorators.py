
from functools import wraps

from flask import _request_ctx_stack, request
from IPy import IP
from functools import wraps
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
                session.rollback()
                raise
            else:
                try:
                    session.commit()
                except:
                    session.rollback()
                    raise
            return result
        return decorated_func
    return decorator

from werkzeug.exceptions import HTTPException, NotFound
def ip_restriction(*iplists):
     ip_int_set = frozenset(
         ip.int()
         for iplist in iplists
         for ip_range_str in ([iplist] if isinstance(iplist,basestring) else iplist)
         for ip in IP(ip_range_str))
##      for x in ip_int_set:
##          print IP(x),
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
 
#from flaskext.decorators import ip_restriction
#@ip_restriction(["192.168.1.0/24"], '127.0.0.1')
     
