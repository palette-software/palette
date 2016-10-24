# Copyright (c) Akiri Solutions, Inc.  All Rights Reserved.
"""
Backend profile store using SQLAlchemy.
"""
from datetime import datetime

from ...sqlalchemy import sqa
from ..mixin import TraceDatabaseMixin
from . import ProfileStore

class DatabaseProfileStore(ProfileStore, TraceDatabaseMixin):
    """
    Store profile information into a database backend.
    """
    # pylint: disable=too-few-public-methods

    def __init__(self):
        self.trace_create_all()

    def save(self, path_info, entries):
        """Commit a set of records to the database."""
        # entries are heavily preprocessed due to the way they are inserted
        # and the search requirements.
        if not entries:
            # this can't really happen in practice.
            return

        # epoch seconds
        started_at = entries[0].timestamp
        ended_at = entries[-1].timestamp
        duration = ended_at - started_at

        # convert to datetime instances
        started_at = datetime.utcfromtimestamp(started_at)
        ended_at = datetime.utcfromtimestamp(ended_at)

        connection = sqa.connect()
        try:
            with connection.begin():
                result = connection.execute(self.traces_table.insert(),
                                            path_info=path_info,
                                            started_at=started_at,
                                            ended_at=ended_at,
                                            duration=duration)
                traceid = result.inserted_primary_key[0]
                for entry in entries:
                    timestamp = datetime.utcfromtimestamp(entry.timestamp)
                    connection.execute(self.trace_events_table.insert(),
                                       traceid=traceid,
                                       name=entry.name(),
                                       event=entry.event,
                                       timestamp=timestamp)
        finally:
            connection.close()
