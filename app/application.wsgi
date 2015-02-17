#!/usr/bin/env python
# pylint: disable=invalid-name

from __future__ import absolute_import
import os

from paste.auth.auth_tkt import AuthTKTMiddleware
from paste.proxy import Proxy

from akiri.framework.admin import LogoutApplication
from akiri.framework.middleware.auth import AuthForbiddenMiddleware
from akiri.framework.middleware.auth import AuthRedirectMiddleware
from akiri.framework.route import Router
from akiri.framework.middleware.sqlalchemy import SessionMiddleware

from palette import HomePage, set_aes_key_file
from palette.admin import LoginApplication, LoginPage
from palette.about import AboutPage
from palette.expire import ExpireMiddleware
from palette.initial import OpenApplication, InitialMiddleware
from palette.manage import ManagePage
from palette.profile import ProfilePage
from palette.request import BaseMiddleware, RemoteUserMiddleware
from palette.routing import RestRouter, ConfigureRouter
from palette.setup import SetupPage
from palette.workbooks import WorkbookArchive, WorkbookData

# settings
if __name__ == '__main__':
    BASEDIR = os.path.dirname(os.path.abspath(__file__))
    AES_KEY_FILE = os.path.expanduser('~/.aes')
else:
    BASEDIR = '/var/palette'
    AES_KEY_FILE = '/var/palette/.aes'
SHARED = 'tableau2014'
LOGIN_URL = '/login'
LOGIN_MAX_AGE = 2592000
LICENSING_URL = 'https://licensing.palette-software.com/hello'
WORKBOOK_DATA_PATH = os.path.join(BASEDIR, 'data', 'workbook-archive')
DATABASE = 'postgresql://palette:palpass@localhost/paldb'

# general configuration
set_aes_key_file(AES_KEY_FILE)

# individual apps
licensing_proxy = Proxy(LICENSING_URL, allowed_request_methods=['GET'])
loginapp = LoginApplication(secret=SHARED,
                            max_age=LOGIN_MAX_AGE,
                            httponly=True)

# remote_user -> auth_tkt -> 403 -> rest
rest = RestRouter()
rest = RemoteUserMiddleware(rest)
rest = AuthForbiddenMiddleware(rest)
rest = AuthTKTMiddleware(rest, secret=SHARED)

# auth_tkt -> initial -> expire -> auth -> page
pages = Router()
pages.add_route(r'/about\Z|/support/about\Z', AboutPage())
pages.add_route(r'/workbook/archive\Z', WorkbookArchive())
pages.add_route(r'/manage\Z', ManagePage())
pages.add_route(r'/profile\Z', ProfilePage())
pages.add_route(r'/configure/', ConfigureRouter())
pages.add_route(r'/data/workbook-archive\Z', WorkbookData(WORKBOOK_DATA_PATH))
pages.add_route(r'/setup\Z', SetupPage())
pages.add_route(r'/licensing\Z', licensing_proxy)
pages.add_route(r'/', HomePage())
pages = RemoteUserMiddleware(pages)
pages = AuthRedirectMiddleware(pages, redirect=LOGIN_URL)
pages = ExpireMiddleware(pages)
pages = InitialMiddleware(pages)
pages = AuthTKTMiddleware(pages, secret=SHARED)

# top-level, first called router
router = Router()
router.add_route(r'/open/setup\Z', OpenApplication(secret=SHARED))
router.add_route(r'/rest/', rest)
router.add_route(LOGIN_URL + r'\Z', LoginPage())
router.add_route(LOGIN_URL + r'/authenticate\Z', loginapp)
router.add_route(r'/logout', LogoutApplication(redirect=LOGIN_URL))
router.add_route(r'/', pages)

# session -> base  -> main-router
application = BaseMiddleware(router)
application = SessionMiddleware(DATABASE, app=application,
                                echo=False, max_overflow=45)

if __name__ == '__main__':
    from webob.static import DirectoryApp
    from akiri.framework.server import runserver

    # logging that would normally be handled by the webserver
    from paste.translogger import TransLogger
    application = TransLogger(application)

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

    runserver(application, use_reloader=True)
