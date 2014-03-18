import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import sessionmaker
from controller import meta

from akiri.framework.config import store
from akiri.framework.api import MainPage, LoginPage

# Set up database connection (see rfc1738)
url = store.get("database", "url")
echo = store.getboolean("database", "echo", default=False)

meta.engine = sqlalchemy.create_engine(url, echo=echo)
meta.Base.metadata.create_all(bind=meta.engine)

import monitor
import backup
import manage

class DashboardPage(MainPage):
    TEMPLATE = 'dashboard.mako'

    def __init__(self, global_conf):
        super(DashboardPage, self).__init__(global_conf)
        self.next = store.get('backup', 'next',
                              default='No backup is scheduled.')

class Login(LoginPage):
    TEMPLATE = 'login.mako'
