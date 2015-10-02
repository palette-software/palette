""" Module to create 'options' i.e. Dropdown configuration """
# pylint: enable=missing-docstring,relative-import

from collections import OrderedDict

DO_NOT_MONITOR = "Do Not Monitor"

class ListOption(object):
    """Generates options for a list of values where the str(id) == value."""
    def __init__(self, name, valueid, valueid_list):
        # assert valueid in valueid_list
        self.name = name
        self.valueid = valueid
        self.valueid_list = valueid_list

    def default(self):
        """ Build the mapping object for this option """
        # This name matches what the JSON encoder expects
        options = []
        for valueid in self.valueid_list:
            options.append({'id': valueid, 'item': str(valueid)})
        return {'name': self.name,
                'id': self.valueid,
                'value': str(self.valueid),
                'options': options}


class DictOption(object):
    """Generates options for an (ordered) dict."""
    def __init__(self, name, valueid, valueid_dict):
        assert valueid in valueid_dict
        self.name = name
        self.valueid = valueid
        self.valueid_dict = valueid_dict

    def default(self):
        """ Build the mapping object for this option """
        # This name matches what the JSON encoder expects
        options = []
        for key in self.valueid_dict:
            options.append({'id': key, 'item': str(self.valueid_dict[key])})
        return {'name': self.name,
                'id': self.valueid,
                'value': str(self.valueid_dict[self.valueid]),
                'options': options}

def _timeopt_display(value, increment):
    """ Build the display string for TimeOption """
    if value == 1:
        return '1 ' + increment
    else:
        return str(value) + ' ' + increment + 's'


class TimeOption(DictOption):
    """Generates options specified by time (e.g. seconds, minutes, hours)"""

    def __init__(self, name, valueid, value_dict):
        result = OrderedDict()
        result[0] = DO_NOT_MONITOR

        if 'seconds' in value_dict:
            for value in value_dict['seconds']:
                if value > 0:
                    result[value] = _timeopt_display(value, 'second')

        if 'minutes' in value_dict:
            for value in value_dict['minutes']:
                if value > 0:
                    result[value*60] = _timeopt_display(value, 'minute')

        if 'hours' in value_dict:
            for value in value_dict['hours']:
                if value > 0:
                    result[value*60*60] = _timeopt_display(value, 'hour')

        assert valueid in result
        super(TimeOption, self).__init__(name, valueid, result)

class PercentOption(DictOption):
    """Generates options specified as percentages. """

    def __init__(self, name, valueid, value_range):
        result = OrderedDict()
        for value in value_range:
            if value > 100:
                result[value] = DO_NOT_MONITOR
            else:
                result[value] = str(value) + '%'
        assert valueid in result
        super(PercentOption, self).__init__(name, valueid, result)
