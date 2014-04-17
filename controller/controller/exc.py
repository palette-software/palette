import httplib

__all__ = [ "HttpException" ]

class HTTPException(httplib.HTTPException):
    def __init__(self, message, body=None):
        Exception.__init__(self, message)

        self.body = body
