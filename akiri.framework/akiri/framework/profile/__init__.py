# Copyright (c) Akiri Solutions, Inc.  All Rights Reserved.
"""
Profiling support for the akiri.framework.
"""
from __future__ import absolute_import
import inspect
import logging
import sys
import threading

# NOTE: change this for windows :
#   http://stackoverflow.com/questions/1938048/high-precision-clock-in-python
import time

logger = logging.getLogger(__name__)

from ..util import qualname
from .store import StreamProfileStore

# pylint: disable=invalid-name
# Thread-local data storage used by the Profiler class.
_localdata = threading.local()
# pylint: enable=invalid-name

def _profiled_object(obj, profiler=None):
    """
    Optionally capture profile information about the specified object.
    The object may be a type (class) or just an instance.
    NOTE: this adds __profiled__ to the object and optionally profiler.
    """
    # pylint: disable=too-many-branches
    if profiler:
        obj.profiler = profiler
    obj.__profiled__ = True
    called = obj.__call__

    def __call__(self, environ, start_response):
        path_info = environ['PATH_INFO']

        if not hasattr(self, '__qualname__'):
            if inspect.isclass(self):
                self.__qualname__ = qualname(self)
            else:
                self.__qualname__ = qualname(self.__class__)

        profiler = None
        if not hasattr(self, 'profiler'):
            self.profiler = None

        if self.profiler:
            profiler = self.profiler
            profiler.start(environ)
        elif '__profiler__' in environ:
            profiler = environ['__profiler__']

        if profiler:
            profiler.profile_enter(app=self.__qualname__)
        try:
            return called(self, environ, start_response)
        finally:
            if profiler:
                profiler.profile_exit(app=self.__qualname__)
                if self.profiler:
                    # This is the top-level profiling object
                    profiler.finish(path_info, environ)

    obj.__call__ = __call__
    return obj

class ProfiledFunction(object):
    """ Wrapper class for profiling a bare WSGI function. """
    # pylint: disable=too-few-public-methods
    def __init__(self, func, profiler=None):
        self.func = func
        self.profiler = profiler
        self.__qualname__ = qualname(self.func)
        self.__profiled__ = True

    def __call__(self, environ, start_response):
        """Wrapper function for a WSGI function."""
        path_info = environ['PATH_INFO']
        profiler = None

        if self.profiler:
            profiler = self.profiler
            profiler.start(environ)
        elif '__profiler__' in environ:
            profiler = environ['__profiler__']
            profiler.profile_enter(app=self.__qualname__)

        try:
            return self.func(environ, start_response)
        finally:
            if profiler:
                profiler.profile_exit(app=self.__qualname__)
                if self.profiler:
                    # This is the top-level profiling object
                    profiler.finish(path_info, environ)

def profiled(obj):
    """
    General purpose decorator to add profiling capablity to a WSGI callable.
    """
    if inspect.isfunction(obj):
        return ProfiledFunction(obj)
    return _profiled_object(obj)


# FIXME: create 'unprofiled' which wraps a callable in WSGI middleware

class ProfileEntry(object):
    """Data point in the profile"""
    # pylint: disable=too-few-public-methods
    def __init__(self, app=None, event=None):
        self.app = app
        self.event = event
        self.timestamp = time.time()

    def name(self):
        """Generate a descriptive name for the application context."""
        if not self.app:
            return None
        if isinstance(self.app, basestring):
            return self.app
        return self.app.__qualname__


class Profiler(object):
    """WSGI profile generator"""

    ENTER = '__enter__'
    EXIT = '__exit__'

    def __init__(self, store=None):
        if store is None:
            self.store = StreamProfileStore()
        else:
            self.store = store

    def profile(self, event, app=None):
        """Generate a profile point."""
        # pylint: disable=no-self-use
        if hasattr(_localdata, 'profile'):
            logmsg = event
            if app:
                if isinstance(app, basestring):
                    logmsg = app + ' ' + event
                else:
                    logmsg = app.name() + ' ' + event
            logger.info(logmsg)
            _localdata.profile.append(ProfileEntry(app=app, event=event))
        else:
            logger.debug('(empty)')

    def profile_enter(self, app=None):
        """Generate a profile ENTER event."""
        return self.profile(self.ENTER, app=app)

    def profile_exit(self, app=None):
        """Generate a profile EXIT event."""
        return self.profile(self.EXIT, app=app)

    @classmethod
    def translate(cls, profiler):
        """
        Convert the specified profiler value into a Profiler object.
        If a bool == True is used, then create a generic Profiler
        """
        if isinstance(profiler, bool):
            if profiler:
                return Profiler()
            else:
                return None
        return profiler

    def start(self, environ):
        """Enable profiling of this thread/request."""
        # pylint: disable=no-self-use
        logger.info('start')
        _localdata.profile = []
        environ['__profile__'] = True
        environ['__profiler__'] = self

    def finish(self, path_info, environ):
        """
        End profiling and save the resulting data.
        `path_info` is passed as a parameter - instead of being pulled from
        the environment since it may change during the application handling.
        """
        entries = self.end()
        if entries:
            # The __profile__ environment variable lets apps -
            # which are particular URLs - opt-out of profiling.
            if '__profile__' in environ and environ['__profile__']:
                self.save(path_info, entries)
        if '__profile__' in environ:
            del environ['__profile__']
        if '__profiler__' in environ:
            del environ['__profiler__']

    def end(self):
        """Disable profiling and return all profile data."""
        # pylint: disable=no-self-use
        logger.info('end')
        result = None
        if hasattr(_localdata, 'profile'):
            result = _localdata.profile
            del _localdata.profile
        return result

    def save(self, url, entries):
        """Send the profiling data for this run to the store."""
        logger.info('save')
        app = None
        for entry in entries:
            if not (entry.app is None) and app != entry.app:
                app = entry.app
            elif entry.app is None:
                entry.app = app
        self.store.save(url, entries)


class SQLProfileHandler(logging.Handler):
    """Logging handler to capture Profile data from SQLAlchemy"""
    def add_record(self, record):
        """Helper method to append the record to the current profiling data."""
        # pylint: disable=no-self-use
        if hasattr(_localdata, 'profile'):
            _localdata.profile.append(ProfileEntry(event=record))

    def filter(self, record):
        msg = self.format(record)
        if msg != '{}':
            self.add_record(msg)
        return False

    def emit(self, record):
        pass


class SQLProfiler(Profiler):
    """Profiler class to capture all SQL statements emitted by SQLAlchemy."""
    def __init__(self, store=None, handler=None):
        super(SQLProfiler, self).__init__(store=store)

        # The sqlalchemy.engine becomes the sole domain of this object.
        self.logger = logging.getLogger('sqlalchemy.engine')
        self.logger.handlers = []
        self.logger.addHandler(logging.NullHandler())
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        if handler is None:
            self.handler = SQLProfileHandler()
        else:
            self.handler = handler

    def start_logger(self):
        """
        Enable the logger which generates SQL statements.
        This method may be overridden to provide additional data.
        """
        self.logger.addHandler(self.handler)

    def remove_logger(self):
        """
        Disable the logger which generates SQL statements.
        This method may be overridden to provide additional data.
        """
        self.logger.removeHandler(self.handler)

    def start(self, environ):
        self.start_logger()
        super(SQLProfiler, self).start(environ)

    def end(self):
        self.remove_logger()
        return super(SQLProfiler, self).end()
