from akiri.framework.config import store
from akiri.framework.api import MainPage, LoginPage

import akiri.framework.ext.sqlalchemy

import auth
import monitor
import backup
import environment
import manage
import event
import workbooks
import yml
import request

from page import PalettePageMixin

class DashboardPage(MainPage, PalettePageMixin):
    TEMPLATE = 'dashboard.mako'
    active = 'home'

    def render(self, req, obj=None):
        obj = self.preprocess(req, obj)
        return super(MainPage, self).render(req, obj=obj)

class Login(LoginPage):
    TEMPLATE = 'login.mako'

