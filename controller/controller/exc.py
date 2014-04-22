import httplib

__all__ = [ "HTTPException" ]

class HTTPException(httplib.HTTPException):
    def __init__(self, status, reason, body=None):
        message = str(status) + ' ' + reason
        httplib.HTTPException.__init__(self, message)
        self.status = status
        self.reason = reason
        self.body = body
