#!/usr/bin/env python
# pylint: disable=invalid-name

from __future__ import absolute_import
import os

from paste.auth.auth_tkt import AuthTKTMiddleware

from akiri.framework import Application, env
from akiri.framework.admin import LogoutApplication
from akiri.framework.middleware.auth import AuthForbiddenMiddleware
from akiri.framework.middleware.auth import AuthRedirectMiddleware
from akiri.framework.route import Router
from akiri.framework.sqlalchemy import create_engine
from akiri.framework.middleware.sqlalchemy import SessionMiddleware

from palette import HomePage, set_aes_key_file
from palette.admin import LoginApplication, LoginPage
from palette.about import AboutPage
from palette.backup import BackupApplication
from palette.expire import ExpireMiddleware
from palette.initial import InitialSetupPage, InitialSetupApplication
from palette.initial import InitialMiddleware
from palette.manage import ManagePage, ManageApplication
from palette.profile import ProfilePage
from palette.proxy import LicensingProxy
from palette.request import BaseMiddleware, RemoteUserMiddleware
from palette.routing import RestRouter, ConfigureRouter
from palette.state import StateApp
from palette.workbooks import WorkbookArchive, WorkbookData
from palette.datasources import DatasourceArchive, DatasourceData

# settings
if __name__ == '__main__':
    BASEDIR = os.path.dirname(os.path.abspath(__file__))
else:
    BASEDIR = '/var/palette'
AES_KEY_FILE = '/var/palette/.aes'
SHARED = 'tableau2014'
LOGIN_URL = '/login'
LOGIN_MAX_AGE = 2592000
WORKBOOK_DATA_PATH = os.path.join(BASEDIR, 'data', 'workbook-archive')
DATASOURCE_DATA_PATH = os.path.join(BASEDIR, 'data', 'datasource-archive')
DATABASE = 'postgresql://palette:palpass@localhost/paldb'

# general configuration
set_aes_key_file(AES_KEY_FILE)

# individual apps
loginapp = LoginApplication(secret=SHARED,
                            max_age=LOGIN_MAX_AGE,
                            httponly=True)
loginpage = LoginPage()
loginpage = ExpireMiddleware(loginpage)
loginpage = InitialMiddleware(loginpage)


# remote_user -> auth_tkt -> 403 -> rest
rest = RestRouter()
rest = RemoteUserMiddleware(rest)
rest = AuthForbiddenMiddleware(rest)
rest = AuthTKTMiddleware(rest, secret=SHARED)

# the API - this is a subset of the the /rest interface
api = Router()
api.add_route(r'/state\Z', StateApp())
api.add_route(r'/manage\Z', ManageApplication())
api.add_route(r'/backups(/(?P<id>[\d]+))?\Z', BackupApplication())
api = RemoteUserMiddleware(api)
api = AuthForbiddenMiddleware(api)
api = AuthTKTMiddleware(api, secret=SHARED)

# auth_tkt -> initial -> expire -> auth -> page
pages = Router()
pages.add_route(r'/about\Z|/support/about\Z', AboutPage())
pages.add_route(r'/workbook/archive\Z', WorkbookArchive())
pages.add_route(r'/datasource/archive\Z', DatasourceArchive())
pages.add_route(r'/manage\Z', ManagePage())
pages.add_route(r'/profile\Z', ProfilePage())
pages.add_route(r'/configure/', ConfigureRouter())
pages.add_route(r'/data/workbook-archive/(?P<name>[^\s]+)\Z',
                WorkbookData(WORKBOOK_DATA_PATH))
pages.add_route(r'/data/datasource-archive/(?P<name>[^\s]+)\Z',
                DatasourceData(DATASOURCE_DATA_PATH))
pages.add_route(r'/', HomePage())
pages = RemoteUserMiddleware(pages)
pages = AuthRedirectMiddleware(pages, redirect=LOGIN_URL)
pages = ExpireMiddleware(pages)
pages = InitialMiddleware(pages)
pages = AuthTKTMiddleware(pages, secret=SHARED)

# top-level, first called router
router = Router()
router.add_route(r'/licensing\Z', LicensingProxy())
router.add_route(r'/open/setup\Z', InitialSetupApplication(secret=SHARED))
router.add_route(r'/setup\Z', InitialSetupPage())
router.add_route(r'/rest/', rest)
router.add_route(r'/api/v1/', api)
router.add_route(LOGIN_URL + r'\Z', loginpage)
router.add_route(LOGIN_URL + r'/authenticate\Z', loginapp)
router.add_route(r'/logout', LogoutApplication(redirect=LOGIN_URL))
router.add_route(r'/', pages)

# session -> base  -> main-router
application = BaseMiddleware(router)

engine = create_engine(DATABASE, echo=False, max_overflow=45)
application = SessionMiddleware(app=application, bind=engine)
application = Application(application)

if __name__ == '__main__':
    import argparse
    from webob.static import DirectoryApp

    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default=None)
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()

    # logging that would normally be handled by the webserver
    from paste.translogger import TransLogger
    application = TransLogger(application)

    # debugging API
    from akiri.framework.servers import MapApplication
    router.prepend_route(r'/api/map', MapApplication())

    try:
        # pylint: disable=no-name-in-module
        # pylint: disable=import-error
        from akiri.framework.sqlalchemy.application import ConnectionApplication
        router.prepend_route(r'/api/sqlalchemy/connections',
                             ConnectionApplication())
    except ImportError:
        pass

    # serve static content
    docroot = os.path.dirname(os.path.abspath(__file__))
    cssdir = os.path.join(docroot, 'css')
    router.prepend_route(r'/css/', DirectoryApp(cssdir), profile=False)
    fontdir = os.path.join(docroot, 'fonts')
    router.prepend_route(r'/fonts/', DirectoryApp(fontdir), profile=False)
    jsdir = os.path.join(docroot, 'js')
    router.prepend_route(r'/js/', DirectoryApp(jsdir), profile=False)
    imgdir = os.path.join(docroot, 'images')
    router.prepend_route(r'/images/', DirectoryApp(imgdir), profile=False)
    dbgdir = os.path.join(docroot, 'd')
    router.prepend_route(r'/d/', DirectoryApp(dbgdir), profile=False)
    router.prepend_route(r'/env\Z', env, profile=False)

    # reloader setup
    from akiri.framework import reloader
    reloader.watch_dir('less')
    reloader.install()

    import paste.httpserver
    paste.httpserver.serve(application, host=args.host, port=args.port)
