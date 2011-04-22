# encoding: utf-8

from flask import url_for, redirect
from functools import wraps

from flask import request, session, jsonify
from json import loads
from pprint import pprint
from werkzeug.exceptions import HTTPException

class HTTPExceptionWithResponse(HTTPException):
    def __init__(self, response):
        self._response = response
        super(HTTPExceptionWithResponse, self).__init__()
    @property
    def code(self):
        print self._response.status_code
        return self._response.status_code
    def get_response(self, environ):
        return self._response
    
class RedirectToException(HTTPExceptionWithResponse):
    def __init__(self, *args, **kws):
        super(RedirectToException, self).__init__(
            response=redirect_to(*args, **kws))

def redirect_to(*args,**kws):
    code = kws.pop("code",302)
    return redirect(url_for(*args,**kws),code=code)

def receive_json():
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kws):
            if request.method == "POST":
                posted = request.stream.read()
                jsondata = loads(posted)
            else:
                jsondata = loads(request.args['data'])
            kws.update(jsondata)
            return f(*args,**kws)
        return decorated
    return decorator

CC = 31
from struct import pack,unpack
from base64 import urlsafe_b64encode,urlsafe_b64decode
import struct
from datetime import datetime
epoch = datetime(1970, 1, 1)
def dt2int(dt):
    td = dt - epoch
    return int(td.total_seconds())

def urlsafe_pack_ulong(n):
    s = pack("L",n)
    return urlsafe_b64encode(s)[:-2]

def urlsafe_pack_ulonglong(n):
    s = pack("Q",n)
    return urlsafe_b64encode(s)[:-1]

def encode_id(n, k=CC):
    c = n * k % 256
    n = n ^ sum((c * (x + 1) & 255) << 8* x for x in range(8))
    s = pack("Q",n)
    s = s + chr(c)
    return urlsafe_b64encode(s)

def decode_id(s64, k=CC):
    if isinstance(s64,unicode):
        s64 = s64.encode("utf-8")
    try:
        s = urlsafe_b64decode(s64)
    except TypeError,e:
        #raise
        print "::::1::::", s64
        return None
    c = ord(s[-1])
    body = s[:-1]
    try:
        n_tup = unpack("Q", body)
    except struct.error, e:
        #raise
        print "::::2::::", s64
        return None
    if not n_tup:
        print "::::3::::", s64
        return None
    n = n_tup[0]
    n = n ^ sum((c * (x + 1) & 255) << 8 * x for x in range(8))
    if not ord(s[-1]) == n * k % 256:
        print "::::4::::", s64
        print "::::4::::", n
        return None
    return n

def drop_all_tables(metadata, engine):
    con = engine.connect()
    for v in metadata.tables.values():
        if v.exists():
            if engine.name == "postgresql":
                con.execute(("""DROP TABLE %s CASCADE""" % v.name))
            else:
                v.drop(checkfirst=True)

def create_obj(model, argnames, data):
    return [model(**dict(zip(argnames, cols))).save()
                   for cols in data]


def reset_tables():
    from flask import current_app
    db=current_app.db
    db.metadata.bind = db.engine
    db.metadata.drop_all()
    db.metadata.create_all()
    
if __name__ == "__main__":
    print get_username()
    for x in range(1,10):
        print x, encode_id(x)
    for x in range(8):
        n = 256**x + x ** 3 + x
        print "%20d"%n,
        print "%20d"%decode_id(encode_id(n)), decode_id(encode_id(n)) == n, encode_id(n)
    assert decode_id("2") is None
