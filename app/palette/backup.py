import time

from webob import exc

from akiri.framework.api import RESTApplication

__all__ = ["BackupApplication"]

class BackupApplication(RESTApplication):

    NAME = 'backup'

    scheduled = 'Thursday, November 7 at 12:00 AM'

    def handle_backup(self):
        now = time.strftime('%A, %B %d at %I:%M %p')
        return {'last': now,
                'next': self.scheduled }

    def handle_restore(self):
        now = time.strftime('%A, %B %d at %I:%M %p')
        return {'last': now,
                'next': self.scheduled }

    def handle(self, req):
        if req.method == 'GET':
            return {'last': 'Thursday, November 7 at 12:00 AM',
                    'next': self.scheduled}
        elif req.method == 'POST':
            if 'action' not in req.POST:
                raise exc.HTTPBadRequest()
            action = req.POST['action'].lower()
            if action == 'backup':
                return self.handle_backup()
            elif action == 'restore':
                return self.handle_restore()
            raise exc.HTTPBadRequest()
        raise exc.HTTPMethodNotAllowed()
