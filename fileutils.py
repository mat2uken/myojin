# coding: utf-8

class SizeLimitException(Exception):
    pass

def default_stream_factory(total_content_length, filename, content_type,
                           content_length=None):
    """The stream factory that is used per default."""
    if total_content_length > 1024 * 500:
        return TemporaryFile('wb+')
    return StringIO()

class LimitedFileWrapper(object):
    def __init__(self, file, limit):
        self.file = file
        self.size = 0
        self.limit = limit

    def write(self, s):
        self.size += len(s)
        if self.limit < self.size:
            raise SizeLimitException()
        return self.file.write(s)

    def __getattr__(self, name):
        return getattr(self.file, name)

class GeneratorFileWrapper(object):
    def __init__(self, gen):
        gen.next()
        self.gen = gen

    def write(self, s):
        return self.gen.send(s)

    def seek(self, n=0):
        return

def gentest():
    a = yield 12
    b = yield 13
    print a,b
    return

if __name__=="__main__":
    
    g = gentest()
    from pprint import pprint
    pprint(dir(g))
    print g.next()
    print g.send(1)
    print g.send(2)
