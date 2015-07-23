import subprocess
import socket
import sys
import traceback
from datetime import datetime
import tz
import dateutil.parser

UTCFMT = "%Y-%m-%d %H:%M:%SZ"
DATEFMT = "%I:%M%p %Z %b %d, %Y"
SIZEFMT = "%(value).1f%(symbol)s"
SYMBOLS = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

UNDEFINED = "NONE"

# pylint: disable=invalid-name

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
            # pylint: disable=unused-variable
            value = float(n) / prefix[symbol] # used by locals()
            return fmt % locals()
    return fmt % dict(symbol=SYMBOLS[0], value=n)

def _parseutc(s):
    if s is None:
        return None
    return dateutil.parser.parse(s)

# WARNING: deprecated, don't use in new code.
def utc2local(t):
    t = t.replace(tzinfo=tz.tzutc())
    return t.astimezone(tz.tzlocal())

def odbc2dt(s):
    if s is None:
        return None
    dt = _parseutc(s)
    return dt.replace(tzinfo=None)

# FIXME: the import can never work...
def version():
    try:
        # pylint: disable=import-error
        from version import VERSION
        return VERSION
    except ImportError:
        pass
    cmd = 'git rev-parse HEAD 2>/dev/null'
    try:
        head = subprocess.check_output(cmd, shell=True).strip()
    except subprocess.CalledProcessError:
        return 'UNKNOWN'

    cmd = 'git name-rev --tags --name-only --no-undefined '+head+' 2>/dev/null'
    try:
        output = subprocess.check_output(cmd, shell=True)
        return output.strip()
    except subprocess.CalledProcessError:
        pass
    return head

def builddate():
    try:
        # pylint: disable=import-error
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
# returns a float.
def timedelta_total_seconds(t2, t1):
    td = t2 - t1
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 1e6

# reverse of dateime.utcfromtimestamp()
def utctotimestamp(dt, epoch=datetime(1970, 1, 1)):
    return timedelta_total_seconds(dt, epoch)

def safecmd(cmd):
    """Hackish function to obscure passwords in debug output (e.g. tabcmd)"""
    tokens = []
    obscure = False
    for x in cmd.split():
        if x == '--password':
            obscure = True
            tokens.append(x)
            continue
        if obscure:
            tokens.append('<>')
        else:
            tokens.append(x)
        obscure = False
    return ' '.join(tokens)

def is_ip(spec):
    """Returns True if passed 'spec' is an IP address and False if not."""

    try:
        socket.inet_aton(spec)
        return True
    except socket.error:
        return False

def hostname_only(hostname):
    """If hostname is a fqdn, returns only the hostname.
       If hostname is passed without a domain, returns hostname unchanged."""

    dot = hostname.find('.')
    if dot != -1:
        return hostname[:dot]
    else:
        return hostname

def traceback_string(all_on_one_line=True):
    exc_type, exc_value, exc_traceback = sys.exc_info()
    tback = traceback.format_exception(exc_type, exc_value, exc_traceback)

    tback = ''.join(tback)

    if all_on_one_line:
        return tback.replace('\n', '')
    else:
        return tback

def safe_int(value, default=None):
    try:
        return int(value)
    except StandardError:
        pass
    return default

def upgrade_rwlock(f):
    """Decorator.
       Gets a read lock from the upgrade_rwlock.
    """
    def realf(self, *args, **kwargs):
        self.server.upgrade_rwlock.read_acquire()
        try:
            return f(self, *args, **kwargs)
        finally:
            self.server.upgrade_rwlock.read_release()
    return realf

def extend(dict1, dict2):
    """
    Add the contents of dict2 to dict1 and return the result.
    The name is the same as the jQuery function with the same purpose.
    """
    for key in dict2:
        value2 = dict2[key]
        if key in dict1:
            if hasattr(value2, '__getitem__') \
                    and not isinstance(value2, basestring):
                dict1[key] += value2
            else:
                raise KeyError("'" + key + "' exists.")
        else:
            dict1[key] = value2
    return dict1
