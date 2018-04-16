# Copyright (c) Akiri Solutions, Inc.  All Rights Reserved.
"""Utility funcitons available in the `akiri.framework`"""

# from __future__ import absolute_import
import os
import binascii
import inspect
from datetime import datetime
from webob import exc

def str2bool(arg):
    """Convert a string representation to a boolean value."""
    if not arg:
        return False
    arg = str(arg).lower()
    if arg == 'true' or arg == '1' or arg == "yes":
        return True
    return False

# FIXME: redundant code in api.py.
def qualname(obj):
    """Simulates __qualname__ which is introduced in 3.3"""
    if hasattr(obj, '__qualname__'):
        return obj.__qualname__
    if inspect.isclass(obj):
        cls = obj
    else:
        cls = obj.__class__
        if hasattr(cls, '__qualname__'):
            obj.__qualname__ = cls.__qualname__
            return obj.__qualname__
    module = cls.__module__
    name = cls.__name__
    if name.startswith(module):
        return name
    value = module + "." + name
    cls.__qualname__ = value
    if obj != cls:
        obj.__qualname__ = value
    return value

# https://docs.python.org/2/library/datetime.html#datetime.timedelta.total_seconds
def timedelta_total_seconds(ts2, ts1):
    """
    Backport of timedelta.total_seconds() introduced in 2.7.
    Returns a float.
    """
    # pylint: disable=invalid-name
    td = ts2 - ts1
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 1e6

def utctotimestamp(dtime, epoch=datetime(1970, 1, 1)):
    """Reverse of dateime.utcfromtimestamp()"""
    return timedelta_total_seconds(dtime, epoch)

def usec(secs):
    """Convert seconds represented as a float to an integer microseconds."""
    return int(secs * 1e6)

def required_parameters(*params, **kwargs):
    """Decorator to require request parameters."""
    if 'allowed_methods' in kwargs:
        allowed_methods = kwargs['allowed_methods']
        del kwargs['allowed_methods']
    else:
        allowed_methods = None
    if allowed_methods is None:
        allowed_methods = ['POST']
    # FIXME: check that kwargs is empty.
    def wrapper(func):
        # pylint: disable=missing-docstring
        def realf(self, req, *args, **kwargs):
            if not req.method in allowed_methods:
                raise exc.HTTPMethodNotAllowed(req.method)
            for param in params:
                if param not in req.params:
                    raise exc.HTTPBadRequest("'" + param + "' missing")
            return func(self, req, *args, **kwargs)
        return realf
    return wrapper

def generate_token(length=16):
    """Generate a random token of a specified length."""
    return binascii.hexlify(os.urandom(length))
