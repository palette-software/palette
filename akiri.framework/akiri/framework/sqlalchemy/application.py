# Copyright (c) Akiri Solutions, Inc.  All Rights Reserved.
"""SQLAlchemy support for the akiri.framework."""

from __future__ import absolute_import

from .. import GenericWSGIApplication
from . import sqa

class ConnectionApplication(GenericWSGIApplication):
    """Return the state of the SQLAlchemy connection pool."""

    def service_GET(self, req):
        """Return a JSON representation of the Pool state."""
        # pylint: disable=unused-argument
        # pylint: disable=no-self-use
        connections = [entry.todict() for entry in sqa.manager.values()]
        return {'connections': connections}
