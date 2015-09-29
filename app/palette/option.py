""" Module to create 'options' i.e. Dropdown configuration """
# pylint: enable=missing-docstring,relative-import

from collections import OrderedDict

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


class TimeOption(DictOption):
    """Generates options specified by time (e.g. second, minute, hour)"""

    def __init__(self, name, valueid, value_range, increment='second'):
        if not 0 in value_range:
            value_range = [0] + value_range

        if increment == 'second':
            multiplier = 1
        elif increment == 'minute':
            multiplier = 60
        elif increment == 'hour':
            multiplier = 3600
        else:
            raise ValueError("Increment must be 'second', 'minute' or 'hour'")

        valueid_mapping = OrderedDict()
        for value in value_range:
            if value == 0:
                display = "Do Not Monitor"
            elif value == 1:
                display = "1 " + increment
            else:
                display = str(value) + " " + increment + "s"
            valueid_mapping[value * multiplier] = display

        assert valueid in valueid_mapping
        super(TimeOption, self).__init__(name, valueid, valueid_mapping)

class MinuteOption(TimeOption):
    """ TimeOption with 'minute' increments """
    def __init__(self, name, valueid, value_range):
        super(MinuteOption, self).__init__(name, valueid, value_range,
                                           increment='minute')
