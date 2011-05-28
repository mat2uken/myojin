
def pager(xs, current_index, margin=2,getlen=len):
    length = getlen(xs)
    s,e = get_start_end(length,current_index, margin)
    return xs[s:e]

def get_start_end(length, current_index, margin=2):
    w = margin
    start_ = current_index - w
    end_ = current_index + w + 1
    start = max(start_,0)
    end = min(end_, length)
    s = max(start_ - (end_ - end), 0)
    e = min(end_ + (start - start_), length)
    return s, e
    #return xs[s:e]
if __name__ == "__main__":
    xs = "123456789abcdef"
    for x in range(len(xs)):
        print pager(xs, x), xs[x]

