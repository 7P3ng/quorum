def average(xs):
    if not xs:
        raise ValueError('empty sequence')
    return sum(xs) / len(xs)
