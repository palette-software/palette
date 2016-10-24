# Copyright (c) Akiri Solutions, Inc.  All Rights Reserved.
"""
The `akiri.framework` package contains both the API and source for a
creating and running an entire web application.

"""
from __future__ import absolute_import

# These are used by setup.py - don't remove.
__version__ = '0.5.6' # PEP440 compliant
__maintainer__ = 'Akiri Solutions, Inc'
__email__ = 'development@akirisolutions.com'
__url__ = 'http://www.akirisolutions.com'

import json
import logging
import threading
from functools import wraps
from webob import Response, exc

from .request import Request
from .util import qualname

from .profile import Profiler, profiled

logger = logging.getLogger(__name__ + '.main')

# basic test application that shows the environment
def env(environ, start_response):
    """Generic WSGI application to display the application environment"""
    res = Response(body=str(environ))
    res.headers['Content-Type'] = 'application/json'
    return res(environ, start_response)

def required_kwargs(*params):
    """Decorator function to require arguments passed as keywords."""
    def wrapper(func):
        # pylint: disable=missing-docstring
        def wrapped(*args, **kwargs):
            for param in params:
                if param not in kwargs or kwargs[param] is None:
                    raise TypeError("keyword '" + param + "' is required.")
            return func(*args, **kwargs)
        return wrapped
    return wrapper

def filter_with(app, *args):
    """Build a filter pipeline for the specified WSGI application."""
    if not hasattr(app, '__profiled__'):
        app = profiled(app)
    for filterapp in reversed(args):
        filterapp.app = app
        if not hasattr(filterapp, '__profiled__'):
            filterapp = profiled(filterapp)
        app = filterapp
    return app

# These must all start with the same 'framework.' prefix so that they are
# automatically cleaned up at the end of the request by StartResponse.
ENVIRON_PREFIX = 'framework.'
ENVIRON_REQUEST = ENVIRON_PREFIX + 'request'
ENVIRON_RESPONSE = ENVIRON_PREFIX + 'response'
ENVIRON_MAIN = ENVIRON_PREFIX + 'main'
ENVIRON_START_RESPONSE = ENVIRON_PREFIX + 'start_response'

class StartResponse(object):
    """Callable that wraps the passed-in start_response and cleans up the
    request environment."""
    # pylint: disable=too-few-public-methods
    def __init__(self, environ, start_response):
        self.environ = environ
        self.start_response = start_response

    def __call__(self, status, response_headers, exc_info=None):
        for key in self.environ.keys():
            if key.startswith(ENVIRON_PREFIX):
                del self.environ[key]
        return self.start_response(status, response_headers, exc_info)


class GenericWSGI(object):
    """
    Base class for WSGI applications.
    If passed app it acts as transparent middleware, otherwise a 200
    status is returned with an empty body.
    """

    def __init__(self, app=None):
        self.__qualname__ = qualname(self.__class__) # FIXME: use a metaclass
        self.app = app
        logger.debug(self.__qualname__ + '.__init__')

    def make_request(self, environ):
        """
        Create a new Request object.
        This method is only called at most once in a given request lifecycle.
        """
        # pylint: disable=no-self-use
        return Request(environ)

    def _make_request(self, environ):
        """Get or create a webob request for the current environment."""
        if ENVIRON_REQUEST in environ:
            return environ[ENVIRON_REQUEST]
        req = self.make_request(environ)
        environ[ENVIRON_REQUEST] = req
        return req

    def make_response(self, req):
        """Create a new Response object.
        This method is only called once in a given request lifecycle.
        """
        # pylint: disable=no-self-use
        # pylint: disable=unused-argument
        return Response()

    def _make_response(self, req):
        """Get or create a webob response for the request."""
        # pylint: disable=unused-argument
        if ENVIRON_RESPONSE in req.environ:
            return req.environ[ENVIRON_RESPONSE]
        res = self.make_response(req)
        req.environ[ENVIRON_RESPONSE] = res
        return res

    def tokenize_path_info(self, req):
        """Return the components of the current path_info as a list."""
        # pylint: disable=no-self-use
        path_info = req.environ['PATH_INFO']
        if not path_info or path_info == '/':
            return []
        if path_info.startswith('/'):
            path_info = path_info[1:]
        return path_info.split('/')

    def service(self, req):
        """
        Generic request handler, likely overridden by a subclass.
        Returning None calls the next application in the pipeline.
        """
        # pylint: disable=no-self-use
        # pylint: disable=unused-argument
        return None

    def __call__(self, environ, start_response):
        logger.info(self.__qualname__ + '.__call__: ' + environ['PATH_INFO'])

        if ENVIRON_START_RESPONSE not in environ:
            start_response = StartResponse(environ, start_response)
            environ[ENVIRON_START_RESPONSE] = start_response

        req = self._make_request(environ)
        try:
            res = self.service(req)
        except exc.WSGIHTTPException as _exc:
            return _exc(environ, start_response)
        if res is None:
            if self.app:
                return self.app(environ, start_response)
            return env(environ, start_response)
        if callable(res):
            # pylint: disable=not-callable
            return res(environ, start_response)

        data = res
        res = self._make_response(req)
        if isinstance(data, dict):
            res.content_type = 'application/json'
            res.body = json.dumps(data)+'\n'
        else:
            res.body = str(data)
        return res(environ, start_response)

    def filter_with(self, *args):
        """
        Return a new WSGI application with the specified filters applied
        to this application.
        """
        return filter_with(self, *args)


class GenericWSGIApplication(GenericWSGI):
    """Base class for 'leaf' WSGI applications - i.e. non-middleware"""

    def service(self, req):
        for methodname in ('service_' + req.method, req.method.lower()):
            if hasattr(self, methodname):
                func = getattr(self, methodname)
                return func(req)
        raise exc.HTTPMethodNotAllowed()

Endpoint = GenericWSGIApplication

# pylint: disable=invalid-name
# Use this base class if service() is overridden - but not __call__ -
# so that the profiling data is correct.
ProfiledWSGI = profiled(GenericWSGI)
# pylint: enable=invalid-name

class Application(GenericWSGI):
    """Class to create the primary Application object."""

    def __init__(self, app, **kwargs):
        if 'profiler' in kwargs:
            self.profiler = kwargs['profiler']
            del kwargs['profiler']
        else:
            self.profiler = None
        if not hasattr(app, '__profiled__'):
            app = profiled(app)
        if 'filter_path_info' in kwargs:
            filter_path_info = kwargs['filter_path_info']
            if isinstance(filter_path_info, basestring):
                self.filter_path_info = [filter_path_info]
            else:
                self.filter_path_info = filter_path_info
            del kwargs['filter_path_info']
        else:
            self.filter_path_info = []
        super(Application, self).__init__(app=app, **kwargs)

    def __call__(self, environ, start_response):
        assert ENVIRON_MAIN not in environ
        environ[ENVIRON_MAIN] = self

        # The environ gets reused across multiple request handled by the same
        # thread-based worker.  Make sure new Request and Response objects
        # are created for each request.
        assert ENVIRON_REQUEST not in environ
        assert ENVIRON_RESPONSE not in environ

        path_info = environ['PATH_INFO']
        if path_info in self.filter_path_info:
            logger.debug('filtered: ' + path_info)
            res = exc.HTTPNotFound()
            del environ[ENVIRON_MAIN]
            return res(environ, start_response)

        if self.profiler:
            self.profiler = Profiler.translate(self.profiler)

        if not self.profiler is None:
            self.profiler.start(environ)
        try:
            return super(Application, self).__call__(environ, start_response)
        finally:
            if self.profiler:
                self.profiler.finish(path_info, environ)
            # ENVIRON_MAIN is cleaned up by StartResponse
