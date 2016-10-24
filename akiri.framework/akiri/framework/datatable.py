"""
Module for Google datatables.
"""
class DatatableCell(object):
    """Class representing a single cell in a datatable row."""
    # pylint: disable=too-few-public-methods
    def __init__(self, value=None, formatted=None, p=None):
        # pylint: disable=invalid-name
        self.v = value        # raw value
        self.f = formatted    # formatted value
        self.p = p            # style/data

    def todict(self):
        """Convert this cell to a dict()"""
        data = {}
        if not self.v is None:
            data['v'] = self.v
        if not self.f is None:
            data['f'] = self.f
        if not self.p is None:
            data['p'] = self.p
        return data

class DatatableRow(object):
    """Class representing a row in a datatable."""
    # pylint: disable=too-few-public-methods
    def __init__(self):
        self.cells = []

    def todict(self):
        """Convert this row to a dict()"""
        return {'c': [cell.todict() for cell in self.cells]}

class Datatable(object):
    """Class for building datatable representations."""
    def __init__(self, p=None):
        # pylint: disable=invalid-name
        if p is None:
            self.p = {}
        else:
            self.p = dict(p)
        self.rows = []
        self.cols = []

    def add_column(self, datatype, label=None, unique_id=None):
        """
        Add a new column definition to the datatable.
        This is likely only called by the subclass definition
        """
        col = {'type': datatype}
        if not label is None:
            col['label'] = label
        if not unique_id is None:
            # FIXME: check for uniqueness and throw an exception otherwise.
            col['id'] = unique_id
        self.cols.append(col)

    def todict(self):
        """Convert this datatable to a dict()"""
        data = {}
        if self.p:
            data['p'] = self.p
        data['cols'] = self.cols
        data['rows'] = [row.todict() for row in self.rows]
        return data


class OrgChartDatatable(Datatable):
    """Datatable for an organizational chart."""
    def __init__(self, p=None):
        super(OrgChartDatatable, self).__init__(p=p)
        self.add_column('string', 'Name')
        self.add_column('string', 'Parent')
        self.add_column('string', 'Tooltip')

    def add_row(self, cell, parent='', tooltip=''):
        """Add a new row to the datatable."""
        row = DatatableRow()
        row.cells.append(cell)
        row.cells.append(DatatableCell(value=parent))
        row.cells.append(DatatableCell(value=tooltip))
        self.rows.append(row)
        return row
