__all__ = [ "HttpException", "HttpNotFound" ]

class HttpException(StandardError):
    def __init__(self, status_code, reason):
        self.status_code = status_code
        self.reason = reason

class HttpNotFound(HttpException):
    def __init__(self):
        super(HttpNotFound, self).__init__(404, "Not Found")
