from itertools import islice
def nested(n, xs, padding=()):
    it = iter(xs)
    ys = True
    while ys:
        ys = list(islice(it, n))
        if not ys:
            return
        yield ys + ([padding]*(n - len(ys)) if padding != () else [])
