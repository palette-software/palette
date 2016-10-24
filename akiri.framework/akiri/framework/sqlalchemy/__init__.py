# Copyright (c) Akiri Solutions, Inc.  All Rights Reserved.
"""
Helper classes/functions for applications that use SQLAlchemy
"""

from __future__ import absolute_import
import logging
import threading

from sqlalchemy import create_engine as sqlalchemy_create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

from .connection import ConnectionManager

logger = logging.getLogger(__name__)

def require_engine(method):
    """Decorator to ensure the SQLAlchemy engine is already configured."""
    # pylint: disable=missing-docstring
    def realmethod(self, *args, **kwargs):
        if not hasattr(self, 'engine') or not self.engine:
            raise RuntimeError('create_engine() not called.')
        return method(self, *args, **kwargs)
    return realmethod

# pylint: disable=invalid-name
class Model(object):
    """ Base classs """
    # pylint: disable=too-few-public-methods
    pass
Model = declarative_base(cls=Model)
# pylint: enable=invalid-name

class SQLAlchemy(object):
    """Singleton object containing all SQLAlchemy configuration information."""
    Session = scoped_session(sessionmaker())
    Model = Model

    _instance = None
    # This is probably unnecessary in CPython due to the PIL.
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, *args, **kwargs):
        if not hasattr(self, 'engine'):
            self.engine = None
        if not args and not kwargs:
            return
        if self.engine:
            raise RuntimeError('The engine is already configured.')
        # pylint: disable=no-member
        self.engine = sqlalchemy_create_engine(*args, **kwargs)
        SQLAlchemy.Session.configure(bind=self.engine)
        SQLAlchemy.Model.metadata.bind = self.engine
        self.manager = ConnectionManager(self.engine)
        # to be removed later
        self.create_all()

    @require_engine
    def check(self):
        """Simple method to ensure that the instance is configured."""
        pass

    @require_engine
    def create_all(self):
        """Create all tables defined by the ORM."""
        # pylint: disable=no-member
        SQLAlchemy.Model.metadata.create_all(self.engine)

    @require_engine
    def session(self):
        """Return a Session instance."""
        return self.Session()

    @require_engine
    def dispose_session(self):
        """Close the current Session object."""
        return self.Session.remove()

    @require_engine
    def connect(self):
        """Return a SQLAlchemy Connection object."""
        return self.engine.connect()

# global variable pointing to the the singleton instance.
# pylint: disable=invalid-name
sqa = SQLAlchemy()
Base = SQLAlchemy.Model
# deprecated aliases
DBSession = Session = SQLAlchemy.Session # deprecated
# pylint: enable=invalid-name

def create_engine(*args, **kwargs):
    """Create a global Engine instance and return it to the caller."""
    instance = SQLAlchemy(*args, **kwargs)
    return instance.engine

def create_all(*args, **kwargs):
    """Create all tables defined by the ORM."""
    sqa.create_all(*args, **kwargs)

def connection():
    """Get a reference to a connection object."""
    return sqa.connect()

def get_metadata():
    """Get the current metadata for the ORM."""
    sqa.check()
    # pylint: disable=no-member
    return sqa.Model.metadata

def get_session():
    """Return the scoped session instance."""
    return sqa.session()

def session_commit():
    """Get a reference to the current session and commit it. (ORM)"""
    session = get_session()
    session.commit()

def session_rollback():
    """Get a reference to the current session and roll it back. (ORM)"""
    session = get_session()
    session.rollback()

def session_query(*entities, **kwargs):
    """Generate a SQLAlchemy Query object from the current session. (ORM)"""
    session = get_session()
    return session.query(*entities, **kwargs)

def session_add(entry):
    """ Add an object to the current session. (ORM)"""
    session = get_session()
    session.add(entry)

def session_expunge(instance):
    """ Remove all instances from the current session. (ORM)"""
    session = get_session()
    session.expunge(instance)

def session_expunge_all():
    """ Remove all instances from the current session. (ORM)"""
    session = get_session()
    session.expunge_all()

def session_refresh(instance, attribute_names=None, lockmode=None):
    """ Expire and refresh the attributes on the given instance.. (ORM)"""
    session = get_session()
    session.refresh(instance,
                    attribute_names=attribute_names,
                    lockmode=lockmode)

def session_flush(objects=None):
    """ Flush all the object changes to the database. (ORM)"""
    session = get_session()
    session.flush(objects=objects)

# pylint: disable=invalid-name
# short names
connect = connection
commit = session_commit
rollback = session_rollback
query = session_query
add = session_add
expunge = session_expunge
expunge_all = session_expunge_all
refresh = session_refresh
flush = session_flush

#deprecated
get_connection = connection
