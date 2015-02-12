#!/usr/bin/env python
# pylint: disable=invalid-name

from __future__ import absolute_import
import os
from akiri.framework.wsgi import make_wsgi
from akiri.framework.middleware.sqlalchemy import SessionMiddleware
from palette.request import BaseMiddleware

# session -> base -> main

path = os.path.join(os.path.dirname(__file__), 'development.ini')
application = make_wsgi(path)

application = BaseMiddleware(application)

database = 'postgresql://palette:palpass@localhost/paldb'
application = SessionMiddleware(database, app=application,
                                echo=False, max_overflow=45)

if __name__ == '__main__':
    from akiri.framework.server import runserver

    from paste.translogger import TransLogger
    application = TransLogger(application)

    runserver(application, use_reloader=True)
