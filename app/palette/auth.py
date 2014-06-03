from sqlalchemy import func
from akiri.framework.ext.sqlalchemy import meta

from akiri.framework.api import Authenticator
from akiri.framework.auth import AuthFilter

from controller.profile import UserProfile

class TableauAuthenticator(Authenticator):
    
    def authenticate(self, username, password, service='login'):
        return UserProfile.verify(username, password)

class TableauAuthFilter(AuthFilter):

    def __call__(self, environ, start_response):
        if 'REMOTE_USER' in environ:
            user = UserProfile.get_by_name(environ['REMOTE_USER'])
            user.timestamp = func.current_timestamp()
            meta.Session.commit()
            environ['REMOTE_USER'] = user
        return super(TableauAuthFilter, self).__call__(environ, start_response)
