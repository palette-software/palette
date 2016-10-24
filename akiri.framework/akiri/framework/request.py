# Copyright (c) Akiri Solutions, Inc.  All Rights Reserved.
"""
The framework request object - a light wrapper around webob.Request.
"""

import webob

class Request(webob.Request):
    """Light wrapper around webob.Request."""
    # pylint: disable=too-many-public-methods
    def __getattr__(self, name, DEFAULT=object()):
        """ Override __gettarr__ to call a helper method, if specified."""
        try:
            return super(Request, self).__getattr__(name)
        except AttributeError:
            pass
        if hasattr(self, 'getattr') and self.getattr != None:
            return self.getattr(self, name)
        raise AttributeError(name)

    def params_get(self, name, default=None):
        """Get a param with default value."""
        if not name in self.params:
            return default
        return self.params[name]

    def params_getint(self, name, default=None):
        """Get a param as an int with default value."""
        try:
            return int(self.params[name])
        except StandardError:
            pass
        return default

    def params_getfloat(self, name, default=None):
        """Get a param as a float with default value."""
        try:
            return float(self.params[name])
        except StandardError:
            pass
        return default

    def params_getbool(self, name, default=None):
        """Get a param as a boolean with default value."""
        if not name in self.params:
            return default
        value = self.params[name].lower()
        if value == 'true' or value == '1':
            return True
        if value == 'false' or value == '0':
            return False
        return default
