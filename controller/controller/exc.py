import httplib

__all__ = [ "HTTPException" ]

class HTTPException(httplib.HTTPException):
    def __init__(self, status, reason, method='GET', body=None):
        message = str(status) + ' ' + reason
        httplib.HTTPException.__init__(self, message)
        self.method = method
        self.status = status
        self.reason = reason
        self.body = body

class InvalidStateError(StandardError):
    pass
