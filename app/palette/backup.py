import time

from webob import exc

from akiri.framework.api import RESTApplication

__all__ = ["BackupApplication"]

class BackupApplication(RESTApplication):

    NAME = 'backup'

    scheduled = 'Thursday, November 7 at 12:00 AM'

    def handle(self, req):
        if req.method == 'GET':
            return {'last': 'Thursday, November 7 at 12:00 AM',
                    'next': self.scheduled}
        elif req.method == 'POST':
            now = time.strftime('%A, %B %d at %I:%M %p')
            return {'last': now,
                    'next': self.scheduled }
        raise exc.HTTPMethodNotAllowed()
