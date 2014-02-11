import ConfigParser
from ConfigParser import NoSectionError
from ConfigParser import NoOptionError

class Config(ConfigParser.ConfigParser):

    def __init__(self, configfile):
 
        ConfigParser.ConfigParser.__init__(self)

        if configfile != None:
            self.read(configfile)

    def getdef(self, section, option, default):
        try:
            value = self.get(section, option)
            return value
        except (NoSectionError,NoOptionError):
            return default

    def getintdef(self, section, option, default):
        try:
            value = self.getint(section, option)
            return value
        except (NoSectionError,NoOptionError):
            return default

    def getbooleandef(self, section, option, default):
        try:
            value = self.getboolean(section, option)
            return value
        except (NoSectionError,NoOptionError):
            return default


def main():
   
    config = Config(None)

if __name__ == '__main__':

    main()
