# Copyright (c) Akiri Solutions, Inc.  All Rights Reserved.
"""SQLAlchemy support for the akiri.framework."""

# FIXME: move to a profile subdirectory of middleware ?

from __future__ import absolute_import
from datetime import datetime
from webob import exc
#from sqlalchemy.orm import sessionmaker, scoped_session

from .. import GenericWSGI
from ..sqlalchemy import sqa
from ..util import utctotimestamp, timedelta_total_seconds, usec
from ..profile import Profiler
from ..profile.mixin import TraceDatabaseMixin

def todict(row):
    """
    Convert a row returned by an execute() into a dict that can be
    serialized to JSON.
    """
    data = {}
    if row:
        for key, value in row.items():
            if isinstance(value, datetime):
                value = str(value)
            data[key] = value
    return data

class Item(object):
    """Helper class to hold information about a subcomponent of a cell."""
    # pylint: disable=too-few-public-methods
    def __init__(self, event, start_time, end_time=None):
        self.event = event
        self.start_time = start_time
        self.end_time = end_time

    def duration(self):
        """
        Difference between the start and stop times for this item.
        Returns a float value regardless of the time format.
        """
        if self.end_time is None:
            return None
        if isinstance(self.start_time, float):
            return self.end_time - self.start_time
        return timedelta_total_seconds(self.end_time, self.start_time)


class DatatableCell(object):
    """Helper class to hold the contents of a cell in the Datatable."""
    # pylint: disable=too-few-public-methods
    def __init__(self, name, timestamp, cellid=None, parent='', items=None):
        # pylint: disable=too-many-arguments
        self.name = name
        if cellid is None:
            self.cellid = self.name
        else:
            self.cellid = cellid
        self.parent = parent
        if items is None:
            self.items = []
        else:
            self.items = items
        self.timestamp = timestamp
        self.epoch = datetime.utcfromtimestamp(timestamp)

    def todict(self, reftime=0):
        """Convert to a dict() for building a Datatable representation."""
        fmt = self.name
        timeval = usec(self.timestamp - reftime)
        if timeval:
            fmt += '<p>' + str(timeval) + ' usec</p>'
        else:
            fmt += '<p>start</p>'
        if self.items:
            fmt += '<div>'
            for item in self.items:
                fmt += '<div class="sql">' + item.event
                duration = item.duration()
                if not duration is None:
                    fmt += '<p>' + str(usec(duration)) + ' usec</p></div>'
            fmt += '</div>'
        cell = [{'v': self.cellid, 'f': fmt}, {'v': self.parent}, {'v': ''}]
        return {'c': cell}


# FIXME: this is not middleware -> rename Application
class DatatableMiddleware(GenericWSGI, TraceDatabaseMixin):
    """
    Middleware to provide a REST interface to the profile data.
    The data format is a JSON object compatible with the javascript
    Datatable object used by Google Charts.
    """
    def __init__(self, database, **kwargs):
        if 'allow_dir' in kwargs:
            self.allow_dir = bool(kwargs['allow_dir'])
            del kwargs['allow_dir']
        else:
            self.allow_dir = True

        super(DatatableMiddleware, self).__init__(database, app=None)
        self.trace_create_all()

    def handle_dir(self):
        """Output a 'directory' listing of available traces if allowed."""
        with sqa.connect() as connection:
            result = connection.execute(self.traces_table.select())
            traces = [todict(row) for row in result]
            return {'traces':traces}

    def handle(self, traceid):
        """Generate the dict() for a particular trace in Datatable format."""
        data = {'cols':[{'type':'string', 'label':'Name'},
                        {'type':'string', 'label':'Parent'},
                        {'type':'string', 'label':'Tooltip'}]}

        cells = []

        with sqa.connect() as connection:
            stmt = self.traces_table.select().\
                where(self.traces_table.c.traceid == traceid)
            data['p'] = todict(connection.execute(stmt).fetchone())

            stmt = self.trace_events_table.select().\
                where(self.trace_events_table.c.traceid == traceid).\
                order_by(self.trace_events_table.c.timestamp)

            parent = ''
            for row in connection.execute(stmt):
                epoch = utctotimestamp(row.timestamp)
                if row.event in [Profiler.ENTER, Profiler.EXIT]:
                    if cells:
                        cell = cells[-1]
                        if cell.items and cell.items[-1].end_time is None:
                            cell.items[-1].end_time = epoch
                if row.event == Profiler.ENTER:
                    cell = DatatableCell(row.name, epoch,
                                         cellid=row.eventid, parent=parent)
                    cells.append(cell)
                    parent = row.eventid
                    continue
                elif row.event == Profiler.EXIT:
                    continue
                cell = cells[-1]
                if cell.items:
                    cell.items[-1].end_time = epoch
                item = Item(row.event, epoch)
                cell.items.append(item)

        if cells:
            reftime = cells[0].timestamp
            end_time = reftime + data['p']['duration']
            cell = DatatableCell('end', end_time, parent=cells[-1].cellid)
            cells.append(cell)
        else:
            reftime = 0

        data['rows'] = [cell.todict(reftime=reftime) for cell in cells]
        return data

    def service(self, req):
        """Handle the request."""
        if '__profile__' in req.environ:
            # Don't generate more profile data for this request.
            del req.environ['__profile__']
        path_info = self.tokenize_path_info(req)
        if not path_info:
            if self.allow_dir:
                return self.handle_dir()
            else:
                raise exc.HTTPForbidden()
        try:
            traceid = int(path_info[-1])
        except StandardError:
            raise exc.HTTPBadRequest()
        return self.handle(traceid)
