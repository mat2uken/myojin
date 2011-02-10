from functools import wraps

def getattrs(obj, attrnames, default=None):
    attrs = attrnames.split(".")
    return _getattrs(obj, attrs, default)

def _getattrs(obj, attrs, default):
    if not attrs:
        return obj
    attr = attrs[0]
    if attr.startswith("*"):
        attr = attr[1:]
        return _getattrs([
            
            getattr(x, attr) for x in obj if hasattr(x,attr)], attrs[1:], default)

        return [y for x in obj
                 for y in getattr(x, attr, ())]
    if hasattr(obj, attr):
        return _getattrs(getattr(obj, attr), attrs[1:], default)
    it = getattr(obj, '__iter__', None)
    if it:
        return _getattrs([
            getattr(x, attr) for x in it() if hasattr(x,attr)], attrs[1:], default)
    return default

def setattrs(obj, d):
    for k,v in d.items():
        setattr(obj,k,v)

def keyword_only(f):
    @wraps(f)
    def decorated(self, **kws):
        try:
            return f(self,**kws)
        except:
            raise
    decorated = getattr(f,'original', f)
    return decorated
from contextlib import contextmanager

@contextmanager
def transaction(session):
    try:
        #session.begin()
        session.extension.after_begin(session, None,None)
        yield session
        session.flush()
    except:
        session.rollback()
        raise
    else:
        session.commit()
    finally:
        session.remove()

def run(f):
    return f()

def run_with(context):
    def deco(f):
        with context as x:
            return f(x)
    return deco

def run_with_transaction(session):
    return run_with(transaction(session))

