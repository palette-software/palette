
class ListOption(object):
    """Generates options for a list of values where the str(id) == value."""
    def __init__(self, name, valueid, valueid_list):
        # assert valueid in valueid_list
        self.name = name
        self.valueid = valueid
        self.valueid_list = valueid_list

    def default(self):
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
        # This name matches what the JSON encoder expects
        options = []
        for key in self.valueid_dict:
            options.append({'id': key, 'item': str(self.valueid_dict[key])})
        return {'name': self.name,
                'id': self.valueid,
                'value': str(self.valueid_dict[self.valueid]),
                'options': options}
