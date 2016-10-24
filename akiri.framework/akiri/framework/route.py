# Copyright (c) Akiri Solutions, Inc.  All Rights Reserved.
"""
This module implements a generic router middleware for the `akiri.framework`.
"""

# FIXME: move to middleware!

import logging
import re
from collections import OrderedDict
from webob import exc

from . import GenericWSGI, ENVIRON_PREFIX

logger = logging.getLogger(__name__)

class Route(object):
    """Class to hold information about a specified route."""
    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-arguments
    def __init__(self, pattern, app, flags=0,
                 preserve_path_info=False, profile=True):
        self.pattern = pattern
        self.app = app
        self.flags = flags
        self.preserve_path_info = preserve_path_info
        self.profile = profile
        self.compiled_pattern = re.compile(pattern, self.flags)

# FIXME: change to RouteInfo
class RouteMatch(object):
    """Object to hold information about a matched route."""
    # pylint: disable=too-few-public-methods

    def __init__(self, route, path, matched=None, remainder=''):
        self.route = route
        self.path = path
        self.matched = matched
        self.remainder = remainder

class ReRouteMatch(RouteMatch):
    """RouteMatch object built from a regular expression match object."""
    # pylint: disable=too-few-public-methods

    def __init__(self, route, path, match_object):
        super(ReRouteMatch, self).__init__(route, path)
        self.match_object = match_object

        end = match_object.end()
        if end < len(self.path):
            self.matched = self.path[match_object.start():end]
            self.remainder = self.path[end:]
        else:
            self.matched = self.path
        self.match_object = match_object


class RedirectApp(GenericWSGI):
    """WSGI application to send a temporary redirect."""

    def __init__(self, location, append_script_name=True):
        super(RedirectApp, self).__init__()
        self.location = location
        self.append_script_name = append_script_name

    def service(self, req):
        script_name = req.environ['SCRIPT_NAME']
        if script_name == '/':
            location = self.location
        elif location.startswith('/') and self.append_script_name:
            location = script_name + self.location
        else:
            location = self.location
        raise exc.HTTPTemporaryRedirect(location=location)


class Router(GenericWSGI):
    """Handles URL dispatch for particular path."""

    def __init__(self):
        super(Router, self).__init__(app=None)
        self.routes = []

    @property
    def routemap(self):
        """Map of the currently defined routes."""
        data = OrderedDict({})
        for route in self.routes:
            data[route.pattern] = route.app
        return data

    def prepend_route(self, pattern, app, flags=0,
                      preserve_path_info=False, profile=True):
        """Add a new route definition before all existing routes."""
        # pylint: disable=too-many-arguments
        route = Route(pattern, app, flags=flags,
                      preserve_path_info=preserve_path_info,
                      profile=profile)
        self.routes.insert(0, route)
        logger.info('prepend_route: ' + pattern)
        return route

    def prepend_routes(self, patterns, app, flags=0,
                       preserve_path_info=False, profile=True):
        """Add a list of routes for a particular app befor existing routes."""
        # pylint: disable=too-many-arguments
        for pattern in patterns.reverse():
            self.prepend_route(pattern, app, flags=flags,
                           preserve_path_info=preserve_path_info,
                           profile=profile)


    def add_route(self, pattern, app, flags=0,
                  preserve_path_info=False, profile=True):
        """Add a new route definition."""
        # pylint: disable=too-many-arguments
        route = Route(pattern, app, flags=flags,
                      preserve_path_info=preserve_path_info,
                      profile=profile)
        self.routes.append(route)
        logger.info('add_route: ' + pattern)
        return route

    def add_routes(self, patterns, app, flags=0,
                   preserve_path_info=False, profile=True):
        """Add a list of routes for a particular app."""
        # pylint: disable=too-many-arguments
        for pattern in patterns:
            self.add_route(pattern, app, flags=flags,
                           preserve_path_info=preserve_path_info,
                           profile=profile)

    def add_redirect(self, pattern, location, flags=0, append_script_name=True):
        """Make paths matching the pattern redirect to location."""
        app = RedirectApp(location=location,
                          append_script_name=append_script_name)
        route = Route(pattern, app, flags=flags)
        self.routes.append(route)
        logger.info('add_redirect: ' + pattern + ' -> ' + location)
        return route

    def match(self, path):
        """
        Find the application object for a particular URL.
        Returns a RouteMatch object containing the results.
        """
        for route in self.routes:
            match = re.match(route.compiled_pattern, path)
            if not match is None:
                result = ReRouteMatch(route, path, match)
                logger.info("%s matched '%s', remainder='%s'", path,
                            route.pattern, result.remainder)
                return result
            else:
                logger.debug('mismatch ' + path + " '" + route.pattern + "'")
        return None

    def service(self, req):
        """
        Return the application for the specified path or 404 otherwise.
        This function sets both SCRIPT_NAME and PATH_INFO in the environ.
        """
        path = req.environ['PATH_INFO']
        match = self.match(path)
        if match:
            if not match.route.preserve_path_info:
                req.environ['SCRIPT_NAME'] = match.matched
                if match.remainder.startswith('/'):
                    req.environ['PATH_INFO'] = match.remainder
                else:
                    req.environ['PATH_INFO'] = '/' + match.remainder
            if not match.route.profile:
                if '__profile__' in req.environ:
                    del req.environ['__profile__']
            # Add the matched values from the route definition to the environ,
            # prefixed with ENVIRON_PREFIX so that StartResponse will
            # automatically remove them after processing the request.
            # NOTE: raises ValueError if the key already exists.
            for name, value in match.match_object.groupdict().iteritems():
                if value is None:
                    continue
                key = ENVIRON_PREFIX + name
                if key in req.environ:
                    raise ValueError("The key '"+key+"' exists in req.environ")
                req.environ[key] = value

            return match.route.app
        raise exc.HTTPNotFound()

