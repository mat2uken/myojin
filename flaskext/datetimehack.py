import datetime
from abc import ABCMeta

## class MyABC:

##         MyABC.register(tuple)
from datetime import timedelta
class date(object):
    __metaclass__ = ABCMeta
    _today = None
    def __new__(cls, *args, **kws):
        import datetime
        return datetime._date.__new__(datetime._date, *args, **kws)

    @classmethod
    def set_next_day(cls):
        cls.set_today(cls.today() + timedelta(days=1))
    @classmethod
    def today(cls):
        import datetime
        d = cls._today or datetime._date.today()
        return d
        return date(d.year, d.month,d.day)

    @classmethod
    def set_today(cls, dt):
        import datetime
        cls._today = dt
        d = dt
        dd = datetime._datetime(d.year, d.month, d.day)
        datetime.datetime.set_now(dd)

class Datetime(object):
    __metaclass__ = ABCMeta
    _now = None
    def __new__(cls, *args, **kws):
        import datetime
        return datetime._datetime.__new__(datetime._datetime, *args, **kws)
    @classmethod
    def utcfromtimestamp(cls, *args,**kws):
        import datetime
        return datetime._datetime.utcfromtimestamp(*args,**kws)
    @staticmethod
    def today():
        cls = date
        import datetime
        d = cls._today or datetime._date.today()
        return d
    @classmethod
    def now(cls):
        import datetime
        d = cls._now or datetime._datetime.now()
        return d
        return datetime._datetime(d.year, d.month, d.day, d.hour, d.minute, d.second)

    @classmethod
    def set_now(cls, dt):
        cls._now = dt

date.register(datetime.date)
Datetime.register(datetime.datetime)
#datetime.date.a = 1
datetime._date = datetime.date
datetime.date = date
datetime._datetime = datetime.datetime
datetime.datetime = Datetime
#print "hack datetime"
datetime = Datetime

