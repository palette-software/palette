from dateutil import tz

DATEFMT = "%I:%M %p PDT on %b %d, %Y"
SIZEFMT = "%(value).1f%(symbol)s"
SYMBOLS = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

def sizestr(n, fmt=SIZEFMT):
    n = int(n)
    if n < 0:
        raise ValueError('n < 0')
    prefix = {}
    for i, s in enumerate(SYMBOLS[1:]):
        prefix[s] = 1 << (i+1)*10
    for symbol in reversed(SYMBOLS[1:]):
        if n >= prefix[symbol]:
            value = float(n) / prefix[symbol]
            return fmt % locals()
    return fmt % dict(symbol=SYMBOLS[0], value=n)

def utc2local(t):
    t = t.replace(tzinfo=tz.tzutc())
    return t.astimezone(tz.tzlocal())
