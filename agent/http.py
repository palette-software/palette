import os
import httplib
import urlparse
import json
import shutil

from cStringIO import StringIO

class HTTPRequest(object):

    def __init__(self, handler, method):
        self.handler = handler
        self.method = method

        self.parseurl()
        if self.handler.headers.has_key('content-length'):
            self.content_length = int(self.handler.headers['content-length'])
        else:
            self.content_length = 0
        if self.handler.headers.has_key('content-type'):
            self.content_type = self.handler.headers['content-type'].lower()
        else:
            self.content_type = 'text/plain'

        # Pending data that must still be read?
        self.needs_flush = False

        self.json = {}
        if self.content_length:
            if self.content_type == 'application/json' or \
                self.content_type == 'text/json':
                body = self.handler.rfile.read(self.content_length)
                self.json = json.loads(body)
            else:
                self.needs_flush = True
        self.response = HTTPResponse(self)

    def __getattr__(self, name):
        if name == 'rfile':
            if not self.needs_flush:
                return None
            self.needs_flush = False # caller must read all data
            return self.handler.rfile
        raise AttributeError(name)

    def parseurl(self):
        parts = urlparse.urlparse(self.handler.path)
        self.scheme = parts.scheme
        self.netloc = parts.netloc
        self.path = parts.path
        self.params = parts.params
        self.query_string = parts.query
        self.fragment = parts.fragment
        if self.query_string:
            self.query = urlparse.parse_qs(self.query_string)
        else:
            self.query = {}

    def close(self):
        if self.needs_flush:
            self.handler.rfile.read()

class HTTPResponse(object):

    def __init__(self, req=None):
        self.req = req

        self.status_code = 200
        self.content_type = 'text/plain'
        self.content_length = -1
        self.wfile = StringIO()

    def __getattr__(self, name):
        if name == 'handler':
            return self.req.handler
        raise AttributeError(name)

    def setfile(self, wfile):
        self.wfile.close()
        self.wfile = wfile

    def set_content_length(self):
        info = os.fstat(self.wfile)
        self.content_length = info.st_size

    def flush(self):
        self.handler.send_response(self.status_code)
        self.handler.send_header('Content-Type', self.content_type)
        body = None
        if self.content_length == -1:
            body = self.wfile.getvalue()
            self.content_length = len(body)

        self.handler.send_header('Content-Length', self.content_length)
        self.handler.end_headers()
        if not body is None:
            self.handler.wfile.write(body)
        else:
            shutil.copyfileobj(self.wfile, self.handler.wfile,
                               self.content_length)
        self.wfile.close()
        self.handler.close_connection = 0
        

class HTTPException(StandardError, HTTPResponse):
    def __init__(self, status_code, body=None):
        HTTPResponse.__init__(self)
        self.status_code = status_code
        if body:
            self.wfile.write(str(body))

class HTTPBadRequest(HTTPException):
    def __init__(self, body=None):
        super(HTTPBadRequest, self).__init__(httplib.BAD_REQUEST, body)

class HTTPNotFound(HTTPException):
    def __init__(self, body=None):
        super(HTTPNotFound, self).__init__(httplib.NOT_FOUND, body)

class HTTPMethodNotAllowed(HTTPException):
    def __init__(self, body=None):
        super(HTTPMethodNotAllowed, self). \
            __init__(httplib.METHOD_NOT_ALLOWED, body)

