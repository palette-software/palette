from akiri.framework.config import store
from akiri.framework.api import MainPage, LoginPage

import controller.meta
import akiri.framework.ext.sqlalchemy

controller.meta.meta = akiri.framework.ext.sqlalchemy.meta

import auth
import monitor
import backup
import manage
import event
import extracts
import workbooks
import yml

from page import PalettePageMixin

class DashboardPage(MainPage, PalettePageMixin):
    TEMPLATE = 'dashboard.mako'
    active = 'home'

    def __init__(self, global_conf):
        super(DashboardPage, self).__init__(global_conf)
        self.next = store.get('backup', 'next',
                              default='No backup is scheduled.')

class Login(LoginPage):
    TEMPLATE = 'login.mako'

