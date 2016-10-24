# Copyright (c) Akiri Solutions, Inc.  All Rights Reserved.
"""
Tracks connection information
"""

import logging
import threading
from sqlalchemy import event

logger = logging.getLogger(__name__)

def synchronized(method):
    """Decorator to ensure the SQLAlchemy engine is already configured."""
    # pylint: disable=missing-docstring
    def realmethod(self, *args, **kwargs):
        # pylint: disable=protected-access
        with self._lock:
            return method(self, *args, **kwargs)
    return realmethod


class ConnectionEntry(object):
    """Object representing the state of a connection (record)"""
    # pylint: disable=too-few-public-methods
    def __init__(self, connection_record):
        self.record = connection_record
        self.thread = None # id of the thread that last used this record.
        self.active = False
        self.invalidated = False

    def todict(self):
        """Return a dict representation of this object suitable for JSON"""
        data = {'id': id(self), 'active': self.active}
        if self.thread:
            data['thread'] = self.thread
        if self.record.connection is None:
            data['valid'] = False
        else:
            data['valid'] = True
        return data


class ConnectionManager(object):
    """Overall list of all connection states."""
    def __init__(self, engine):
        self._all = {}
        self._active = {} # all currently checked out connections

        # This is probably unnecessary in CPython due to the PIL.
        self._lock = threading.Lock()

        self.engine = engine
        event.listen(self.engine, "checkout", self._checkout)
        event.listen(self.engine, "checkin", self._checkin)
        event.listen(self.engine, "connect", self._connect)
        # event.listen(self.engine, "invalidate", self._invalidate)
        # event.listen(self.engine, "soft_invalidate", self._soft_invalidate)

    @synchronized
    def values(self):
        """Return all connections as the list"""
        return self._all.values()

    @synchronized
    def active(self):
        """Return all active - i.e. non-checked out - connections."""
        return self._active.values()

    @synchronized
    def _checkout(self, dbapi_connection, connection_record, connection_proxy):
        """Handle event.checkout"""
        # pylint: disable=unused-argument
        key = id(connection_record)
        if not key in self._all:
            raise ValueError('connection record not found during checkout.')
        entry = self._all[key]
        self._active[key] = entry
        entry.active = True
        entry.thread = threading.current_thread().name

    @synchronized
    def _checkin(self, dbapi_connection, connection_record):
        """Handle event.checkin"""
        # pylint: disable=unused-argument
        key = id(connection_record)
        if not key in self._all:
            raise ValueError('connection record not found during checkin.')
        entry = self._all[key]
        if not key in self._active or not entry.active:
            raise ValueError('connection record not active during checkin.')
        del self._active[key]
        entry.active = False

        if entry.record.connection is None:
            del self._all[key]

    @synchronized
    def _connect(self, dbapi_connection, connection_record):
        """Handle event.connect"""
        # pylint: disable=unused-argument
        key = id(connection_record)
        self._all[key] = ConnectionEntry(connection_record)

    @synchronized
    def _invalidate(self, dbapi_connection, connection_record, exception):
        """Handle event.invalidate (1.0.3)"""
        # pylint: disable=unused-argument
        key = id(connection_record)
        if not key in self._all:
            raise ValueError('dbapi connection not found during invalidate.')
        del self._all[key]

    @synchronized
    def _soft_invalidate(self, dbapi_connection, connection_record, exception):
        """Handle event.soft_invalidate (0.9.2)"""
        # pylint: disable=unused-argument
        key = id(connection_record)
        if not key in self._all:
            raise ValueError('connection not found during soft invalidate.')
        entry = self._all[key]
        entry.invalidated = True
