"""Application that report the overall system layout."""
from __future__ import absolute_import

from .. import GenericWSGIApplication, ENVIRON_MAIN
from ..datatable import DatatableCell, OrgChartDatatable
from ..util import qualname

class MapApplication(GenericWSGIApplication):
    """Shows the application map in JSON datatable format.

    Addtional dependencies:
      None
    Environment input:
      Required:
        framework.main: Application object
    Environment output:
      None
    """
    def appid(self, app):
        """Generate a unique id for an application."""
        # pylint: disable=no-self-use
        return hex(id(app))

    def add_to_orgchart(self, datatable, app, parent=None, subtitle=None):
        """Recursivelly add an application to the orgchart."""
        if parent is None:
            parent_value = ''
        else:
            parent_value = self.appid(parent)
        value = app.__class__.__name__
        if not subtitle is None:
            value += "<div>" + subtitle + "</div>"
        cell = DatatableCell(self.appid(app), value)
        datatable.add_row(cell, parent_value, qualname(app))
        if hasattr(app, 'routemap'):
            for pattern in app.routemap:
                self.add_to_orgchart(datatable, app.routemap[pattern],
                                     app, pattern)
        elif hasattr(app, 'app') and not app.app is None:
            self.add_to_orgchart(datatable, app.app, app)

    def service_GET(self, req):
        """Return the datatable as JSON"""
        # pylint: disable=invalid-name
        application = req.environ[ENVIRON_MAIN]
        datatable = OrgChartDatatable()
        self.add_to_orgchart(datatable, application)
        return datatable.todict()
