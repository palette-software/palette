
class StaticOptionType(type):
    def __getattr__(cls, name):
        if name == 'ITEMS':
            return cls.items()
        if name == 'OPTIONS':
            options = []
            for key, value in cls.ITEMS.items():
                options.append({'option': value, 'id': key})
            return options
        raise AttributeError(name)

class BaseStaticOption(object):
    __metaclass__ = StaticOptionType

    @classmethod
    def get(cls, req, name, default=0):
        #pylint: disable=no-member
        if name not in req.GET:
            return default
        try:
            value = int(req.GET[name])
        except StandardError:
            return default
        if value not in cls.ITEMS:
            return default
        return value

    @classmethod
    def name(cls, key):
        #pylint: disable=no-member
        if key in cls.ITEMS:
            return cls.ITEMS[key]
        else:
            return None

    @classmethod
    def config(cls, key):
        #pylint: disable=no-member
        return {'name': cls.NAME,
                'options': cls.OPTIONS,
                'id': key,
                'value': cls.name(key)}
