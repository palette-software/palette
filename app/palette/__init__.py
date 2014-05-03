from akiri.framework.config import store
from akiri.framework.api import MainPage, LoginPage

import akiri.framework.ext.sqlalchemy
from controller import meta

class MetaEngine(object):

    def execute(self, statement, *multiparams, **params):
        return akiri.framework.ext.sqlalchemy.engine.execute(statement, \
            *multiparams, **params)

meta.engine = MetaEngine()

class MetaSession(object):
    """ Wrapper class to always return the factory from the framework. """
    def __call__(self):
        return akiri.framework.ext.sqlalchemy.Session()

    def query(self, *args, **kwargs):
        session = self()
        return session.query(*args, **kwargs)

meta.Session = MetaSession()

import monitor
import backup
import manage
import event

class DashboardPage(MainPage):
    TEMPLATE = 'dashboard.mako'
    main_active = 'home'

    def __init__(self, global_conf):
        super(DashboardPage, self).__init__(global_conf)
        self.next = store.get('backup', 'next',
                              default='No backup is scheduled.')

class Login(LoginPage):
    TEMPLATE = 'login.mako'
