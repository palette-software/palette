import os
import ConfigParser as configparser

class Config(object):

    def __init__(self, path):
        self.parser = configparser.ConfigParser()

        if not path:
            raise ValueError(path)
        if not os.path.exists(path):
            raise IOError("File not found : " + path)

        self.path = path
        self.parser.read(path)

    def _get(self, name, section, option, **kwargs):
        if 'default' in kwargs:
            default = kwargs['default']
            have_default = True
            del kwargs['default']
        else:
            have_default = False

        try:
            f = getattr(self.parser, name)
            return f(section, option, **kwargs)
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            if have_default:
                return default
            raise e

    def get(self, section, option, **kwargs):
        return self._get('get', section, option, **kwargs)

    def getint(self, section, option, **kwargs):
        return self._get('getint', section, option, **kwargs)

    def getfloat(self, section, option, **kwargs):
        return self._get('getfloat', section, option, **kwargs)

    def getboolean(self, section, option, **kwargs):
        return self._get('getboolean', section, option, **kwargs)

    def __getattr__(self, name):
        if hasattr(self.parser, name):
            return getattr(self.parser, name)
        else:
            raise AttributeError(name)
