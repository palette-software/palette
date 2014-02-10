import ConfigParser
from ConfigParser import NoSectionError
from ConfigParser import NoOptionError

class Config(ConfigParser.ConfigParser):

    def __init__(self, configfile):
 
        ConfigParser.ConfigParser.__init__(self)

        if configfile != None:
            self.read(configfile)

    def get(self, section, option, default):
        try:
            value = ConfigParser.ConfigParser.get(self, section, option)
            return value
        except (NoSectionError,NoOptionError):
            return default

    def getint(self, section, option, default):
        return int(self.get(section, option, default))

def main():
   
    config = Config(None)

if __name__ == '__main__':

    main()
