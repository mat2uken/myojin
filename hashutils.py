
import random
random.seed()
#import base64
#print base64
#from base64 import urlsafe_b64encode
b64chars = ("abcdefghijklmnopqrstuvwxyz" +
              "ABCDEFGHIJKLMNOPQRSTUVWXYZ" +
              "0123456789-_")
a_chars = "abcdefghijklmnopqrstuvwxyz"
A_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
d_chars = "0123456789"
alphanum = a_chars + A_chars + d_chars
b64chars = (a_chars +
              A_chars +
              d_chars + "-_")

assert len(set(b64chars)) == 64

def split_digits(target, base, num_of_digits):
    n = target
    for y in range(num_of_digits):
        yield n % base
        n = n / base
    assert n == 0

def random_digits(base, num_of_digits):
    target = random.randint(0, base  ** num_of_digits - 1)
    return split_digits(target, base, num_of_digits)

def random_chars(chars, num):
    return "".join(chars[x] for x in random_digits(len(chars), num))

def random_alphanum(num):
    return random_chars(alphanum, num)    

from functools import partial

random_b64str = partial(random_chars, b64chars)

import hmac
from base64 import urlsafe_b64encode as b_encode
from base64 import urlsafe_b64decode as b_decode
from hashlib import *
from time import mktime
from utils import decode_id, encode_id
from datetime import datetime
#mktime(datetime.now().timetuple())
#datetime.fromtimestamp(utils.decode_id(utils.encode_id(int(time.mktime(datetime.now().timetuple())))))
## print encode_id(int(mktime(datetime.now().timetuple())))
## print len(encode_id(int(mktime(datetime.now().timetuple()))))

def urlsafe_hmac_digest(key, msg, dt=None):
    if not dt:
        dt= datetime.now()
    now = encode_id(int(mktime(dt.timetuple())))
    r = hmac.new(key=key,msg=now + msg,digestmod=sha256)
    result = b_encode(r.digest())[:-1]
    assert len(result)==43
    return now +result
from datetime import timedelta
def verify_urlsafe_hmac_digest(dt_digest, key, msg, expiry_timedelta):
    encoded_dt, digest = dt_digest[:12], dt_digest[12:]
    print decode_id(encoded_dt), type(decode_id(encoded_dt)) , encoded_dt
    try:
        dt = datetime.fromtimestamp(float(decode_id(encoded_dt)))
    except:
        dt = datetime.now()
    if len(digest)!=43:
        return False
    test_digest = urlsafe_hmac_digest(key, msg, dt)
    return test_digest == dt_digest and (datetime.now() < dt + expiry_timedelta )

if __name__=="__main__":
    print random_chars("abc", 3)
    kms=[("KEY", "ABCDEFG"), ("KeY", "ABCDEFG"), ("KEY", "ABCDEFGH"), ]
##     for key,msg in kms:
##         d = urlsafe_hmac_digest(key, msg)
        #print d, len(d)
    key = "key"
    msg = "msg"
    d = urlsafe_hmac_digest(key, msg)
    td = timedelta(days=1)
    print verify_urlsafe_hmac_digest(d,key,msg, td)
    import sys
    print d,len(d)
    #print d
    #sys.exit()
    print '-----'
    print '-----'
    print urlsafe_hmac_digest(*kms[0])
    assert verify_urlsafe_hmac_digest(
        urlsafe_hmac_digest(*kms[0]),
        *kms[0] + (td,))
    assert not verify_urlsafe_hmac_digest(
        urlsafe_hmac_digest(*kms[0]),
        *kms[0] + (timedelta(days=0),))
    assert not verify_urlsafe_hmac_digest(
        urlsafe_hmac_digest(*kms[1]),
        *kms[0] + (td,))
    assert not verify_urlsafe_hmac_digest(
        urlsafe_hmac_digest(*kms[0]),
        *kms[2] + (td,))
    
    num = 3
    base = 3
    for x in range(10):
        target = n = random.randint(0, base ** num - 1)
        print "%10d" % n,
        for y in range(num):
            print "%10d" % (n % base),
            n = n / base
        print list(split_digits(target, base,num))
        assert n == 0


    for x in range(10):
        assert len(random_b64str(10)) == 10

    ss = set(tuple(random_digits(3, 3)) for x in range(1000))
    assert list(sorted(
        set(tuple(random_digits(3, 3)) for x in range(1000))
                       )) ==[(x,y,z)for x in range(3)
                               for y in range(3)
                               for z in range(3)]
    assert list(sorted(
        set(
        random_chars("abc",3) for x in range(1000))
        )) ==[x+y+z for x in "abc" for y in "abc" for z in "abc"]
    assert set(random_b64str(10)[0] for x in range(1000)) == set(b64chars)
    assert set(random_b64str(10)[-1] for x in range(1000)) == set(b64chars)
