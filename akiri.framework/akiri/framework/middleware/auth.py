# Copyright (c) Akiri Solutions, Inc.  All Rights Reserved.
"""
Helper middleware for authentication (but not authorization)
"""
from __future__ import absolute_import
import posixpath
from webob import exc
from .. import GenericWSGIApplication

class AuthRedirectMiddleware(GenericWSGIApplication):
    """Middleware to ensure a user is logged in.  Otherwise the request is
    redirected to another (provided) URL or a 403 response is returned."""
    def __init__(self, app, redirect=None):
        super(AuthRedirectMiddleware, self).__init__(app)
        self.redirect = redirect

    def service(self, req):
        if 'REMOTE_USER' in req.environ:
            return
        path = posixpath.join(req.environ['SCRIPT_NAME'], req.path_info)
        if path == self.redirect:
            return
        if self.redirect:
            if path and path != '/':
                location = self.redirect + '?location=' + path
            else:
                location = self.redirect
            app = exc.HTTPTemporaryRedirect(location=location)
        else:
            app = exc.HTTPForbidden()
        return app


class AuthForbiddenMiddleware(AuthRedirectMiddleware):
    """Return '403 Forbidden' if there is no valid REMOTE_USER"""
    def __init__(self, app):
        super(AuthForbiddenMiddleware, self).__init__(app, redirect=None)

# aliases
AuthRedirectFilter = AuthRedirectMiddleware
AuthForbiddenFilter = AuthRedirectMiddleware
