# Copyright (c) Akiri Solutions, Inc.  All Rights Reserved.
"""
Helper applications for sending data to other services.
"""

import json
import socket
import webob.exc
from paste.proxy import Proxy
from . import GenericWSGI

class ProxyResponse(object):
    """Callable that can be passed to start_response for the proxy."""
    # pylint: disable=too-few-public-methods
    def __init__(self):
        self.status = None
        self.response_headers = None
        self.exc_info = None
        self.status_code = 0
        self.reason_message = None

    def __call__(self, status, response_headers, exc_info=None):
        self.status = status
        self.response_headers = response_headers
        self.exc_info = exc_info

        try:
            status_code, reason_message = status.split(' ', 1)
            self.status_code = int(status_code)
            self.reason_message = reason_message.strip()
        except StandardError:
            pass

class JSONProxy(GenericWSGI):
    """Generic Proxy class for JSON data."""
    def __init__(self, address, allowed_request_methods=(),
                 suppress_http_headers=()):
        super(JSONProxy, self).__init__()
        self.proxy = Proxy(address,
                           allowed_request_methods=allowed_request_methods,
                           suppress_http_headers=suppress_http_headers)

    def postprocess(self, req, data):
        """Modify the data returned by the proxy."""
        # pylint: disable=no-self-use
        # pylint: disable=unused-argument
        return data

    def service(self, req):
        # Sometimes Content-length isn't set, so we need to look at
        # the content body.
        if req.method == 'POST' and not 'CONTENT_LENGTH' in req.environ:
            req.environ['CONTENT_LENGTH'] = len(req.body)

        proxy_res = ProxyResponse()
        try:
            res = self.proxy(req.environ, proxy_res)
        except (StandardError, socket.error) as exc:
            res = webob.exc.HTTPServiceUnavailable()
            res.comment = str(exc)
            return res
        if proxy_res.status_code != 200:
            # FIXME: return the same response that proxy got instead of 503.
            res = webob.exc.HTTPServiceUnavailable()
            res.comment = proxy_res.status
            return res
        data = json.loads(res[0])
        return self.postprocess(req, data)

