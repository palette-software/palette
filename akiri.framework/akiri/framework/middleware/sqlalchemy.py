# Copyright (c) Akiri Solutions, Inc.  All Rights Reserved.
"""SQLAlchemy support for the akiri.framework."""

from __future__ import absolute_import

from .. import GenericWSGI, ProfiledWSGI, profiled, required_kwargs
from ..sqlalchemy import sqa, logger

ENVIRON_SESSION = 'sqlalchemy.session'

@profiled
class SessionMiddleware(GenericWSGI):
    """Wrap each request in a SQLAlchemy session.

    A SQLAlchemy session is created for each HTTP request that can be used
    by downstream applications.  If the application succeeds, i.e. doesn't
    throw an exception, then the session is committed, otherwise the session
    is rolled back.

    Addtional dependencies:
      None
    Environment input:
      Required:
        None
    Environment output:
      sqlalchemy.session: SQLAlchemy Session object.
    Logger:
      akiri.framework.sqlalchemy
    """
    # pylint: disable=too-few-public-methods
    ENVIRON_SESSION = ENVIRON_SESSION

    def __call__(self, environ, start_response):
        session = sqa.session()
        environ[ENVIRON_SESSION] = session
        try:
            res = self.app(environ, start_response)
            session.commit()
            logger.info('session<0x%x> commit()', id(session))
            return res
        finally:
            # implicitly rollback the session.
            sqa.dispose_session()
            del environ[ENVIRON_SESSION]
            logger.info('DBSession.remove()')


class StatementMiddleware(ProfiledWSGI):
    """Middleware to execute a generic SQL statement"""
    # pylint: disable=super-on-old-class, too-few-public-methods

    required_kwargs('statement')
    def __init__(self, app=None, statement=None, itemname='rows'):
        super(StatementMiddleware, self).__init__(app=app)
        self.statement = statement
        self.itemname = itemname

    def service(self, req):
        """Override GenericWSGI.service()"""
        # pylint: disable=unused-argument
        # pylint: disable=no-member

        rows = []
        connection = sqa.connect()
        try:
            result = connection.execute(self.statement)
            logger.info(self.statement)
            if self.app is None:
                for row in result:
                    rows.append(dict(row))
        finally:
            connection.close()

        # only return data if this is a 'leaf' application
        if not self.app is None:
            return None

        return {self.itemname: rows}
