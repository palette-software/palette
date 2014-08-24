import subprocess
from datetime import datetime
from dateutil import tz

UTCFMT = "%Y-%m-%d %H:%M:%SZ"
DATEFMT = "%-I:%M%p PDT on %b %d, %Y"
SIZEFMT = "%(value).1f%(symbol)s"
SYMBOLS = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

UNDEFINED="*UNDEFINED*"

def success(body):
    return not failed(body)

def failed(body):
    return 'error' in body

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

def parseutc(s):
    if s is None: return None
    return datetime.strptime(s, UTCFMT)

def utc2local(t):
    t = t.replace(tzinfo=tz.tzutc())
    return t.astimezone(tz.tzlocal())

def odbc2dt(s):
    if s is None: return None
    dt = parseutc(s)
    return dt.replace(tzinfo=None)

def version():
    try:
        from version import VERSION
        return VERSION
    except ImportError:
        pass
    cmd = 'git rev-parse HEAD 2>/dev/null'
    try:
        head = subprocess.check_output(cmd, shell=True).strip()
    except subprocess.CalledProcessError:
        return UNKNOWN

    cmd = 'git name-rev --tags --name-only --no-undefined '+head+' 2>/dev/null'
    try:
        output = subprocess.check_output(cmd, shell=True)
        return output.strip()
    except subprocess.CalledProcessError:
        pass
    return head

def builddate():
    try:
        from version import DATE
        return DATE
    except ImportError:
        pass
    return None

def str2bool(s):
    if not s:
        return False
    s = str(s).lower()
    if s == 'true' or s == '1' or s == "yes":
        return True
    return False
    
# analoguous to the 2.7 functionality
# https://docs.python.org/2/library/datetime.html#datetime.timedelta.total_seconds
def timedelta_total_seconds(t2, t1):
    td = t2 - t1
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6
