import httplib
import urlparse
import json

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

        self.body = None
        self.json = {}
        if self.content_length:
            self.readbody()

        self.response = HTTPResponse(self)

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

    def readbody(self):
        self.body = self.handler.rfile.read(self.content_length)
        if self.content_type == 'application/json' or \
                self.content_type == 'text/json':
            self.json = json.loads(self.body)


class HTTPResponse(object):

    def __init__(self, req=None):
        self.req = req

        self.status_code = 200
        self.content_type = 'text/plain'
        self.wfile = StringIO()

    def __getattr__(self, name):
        if name == 'handler':
            return self.req.handler
        raise AttributeError(name)

    def flush(self):
        self.handler.send_response(self.status_code)
        self.handler.send_header('Content-Type', self.content_type)
        body = self.wfile.getvalue()
        self.handler.send_header('Content-Length', len(body))
        self.handler.end_headers()
        if body:
            self.handler.wfile.write(body)
        self.handler.close_connection = 0
        

class HTTPException(StandardError, HTTPResponse):
    def __init__(self, status_code, body=None):
        HTTPResponse.__init__(self)
        self.status_code = status_code
        if body:
            self.wfile.write(str(body))

class HTTPNotFound(HTTPException):
    def __init__(self, body=None):
        super(HTTPNotFound, self).__init__(httplib.NOT_FOUND, body)

class HTTPBadRequest(HTTPException):
    def __init__(self, body=None):
        super(HTTPBadRequest, self).__init__(httplib.BAD_REQUEST, body)
