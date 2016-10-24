# Copyright (c) Akiri Solutions, Inc.  All Rights Reserved.
"""Database format for profile information."""

from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import Integer, Float, String, DateTime

from ..sqlalchemy import create_all, get_metadata

class TraceDatabaseMixin(object):
    """Mixin to profile helper methods for table creation."""
    # pylint: disable=attribute-defined-outside-init

    @classmethod
    def define_traces_table(cls, metadata):
        """Construct the 'traces' table."""
        # FIXME: maybe make a mixin?
        return Table('traces', metadata,
                     Column('traceid', Integer, primary_key=True),
                     Column('path_info', String, nullable=False),
                     Column('started_at', DateTime, nullable=False),
                     Column('ended_at', DateTime, nullable=False),
                     Column('duration', Float, nullable=False))

    @classmethod
    def define_trace_events_table(cls, metadata):
        """Construct the 'trace_event' table."""
        # FIXME: maybe make a mixin?
        return Table('trace_events', metadata,
                     Column('eventid', Integer, primary_key=True),
                     Column('traceid', Integer, ForeignKey("traces.traceid"),
                            nullable=False),
                     Column('name', String, nullable=False),
                     Column('event', String, nullable=False),
                     Column('timestamp', DateTime, nullable=False))


    def trace_create_all(self):
        """
        Instantiate the table objects.
        """
        cls = TraceDatabaseMixin
        metadata = get_metadata()
        self.traces_table = cls.define_traces_table(metadata)
        self.trace_events_table = cls.define_trace_events_table(metadata)
        create_all()
