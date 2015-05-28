from collections import OrderedDict

from util import odbc2dt
from mixin import CredentialMixin

class ODBC(CredentialMixin):

    URI = '/sql'

    DRIVER = '' # filled in later depending on bitness of tableau install
    SERVER = '127.0.0.1'
    PORT = 8060
    DATABASE = 'workgroup'

    def __init__(self, agent):
        self.agent = agent
        self.server = agent.server
        if self.server is None:
            raise RuntimeError("agent.server is None")

    def host(self):
        # worker id points to the 'hot' database IP.
        worker_id = self.server.yml.get('pgsql.worker_id', default=None)
        if worker_id is None:
            return self.SERVER
        key = 'pgsql' + worker_id + '.host'
        return self.server.yml.get(key, default=self.SERVER)

    def _set_driver(self):
        # pylint: disable=invalid-name

        bitness = self.agent.bitness
        if not bitness:
            self.server.log.error("odbc.connection: " + \
                            "Missing yml 'agent.bitness'.  Will use 64-bit.")
        if bitness == 32:
            self.DRIVER = '{PostgreSQL Unicode}'
        else:
            # Default
            self.DRIVER = '{PostgreSQL Unicode(x64)}'
        self.DRIVER = '{PostgreSQL Unicode(x64)}'

    def connection(self):
        # worker id points to the 'hot' database IP.
        worker_id = self.server.yml.get('pgsql.worker_id', default=None)
        if not worker_id is None:
            key = 'pgsql' + worker_id + '.host'
            host = self.server.yml.get(key, default=self.SERVER)
            key = 'pgsql' + worker_id + '.port'
            port = self.server.yml.get(key, default=self.PORT)
        else:
            host = self.SERVER
            port = str(self.PORT)

        if not self.DRIVER:
            self._set_driver()

        cred = self.get_cred(self.agent.envid, self.READONLY_KEY)
        if cred:
            uid = cred.user # Should be 'readonly'
            passwd = cred.getpasswd()
        else:
            uid = 'tblwgadmin'
            passwd = ''

        s = 'DRIVER=' + self.DRIVER +'; '
        s += 'Server=' + host + '; '
        s += 'Port=' + port + '; '
        s += 'Database=' + self.DATABASE + '; '
        s += 'Uid=' + uid + '; '
        s += 'Pwd=' + passwd + ';'
        return s

    def execute(self, stmt):
        data = {'connection': self.connection(),
                'select-statement': stmt}
        return self.server.send_immediate(self.agent, 'POST', self.URI, data)

    @classmethod
    def schema(cls, data):
        d = OrderedDict()
        info = data["$schema"]["Info"]
        for i in xrange(0, len(info), 3):
            column = info[i+1]
            ctype = info[i+2]
            if ctype.startswith('System.'):
                ctype = ctype[7:]
            d[column] = ctype
        return d

    @classmethod
    def load(cls, data):
        schema = cls.schema(data)
        return [ODBCData(schema, row) for row in data['']]


class ODBCData(object):

    def __init__(self, schema, row):
        self.schema = schema
        self.data = OrderedDict()

        i = 0
        for column in self.schema:
            ctype = self.schema[column]
            value = row[i]
            if ctype == 'DateTime':
                if value and value.endswith('Z'): # HACK
                    # convert to true iso8601
                    value = value.replace(' ', 'T')
                self.data[column] = odbc2dt(value)
            else:
                self.data[column] = value
            i += 1

    def copyto(self, obj, excludes=None):
        if excludes is None:
            excludes = []
        for name in self.schema:
            if not name in excludes:
                setattr(obj, name, self.data[name])
        return obj

    def __repr__(self):
        values = []
        for column in self.data:
            s = '(' + column + ',' + \
                str(self.data[column]) + ',' + \
                self.schema[column] + ')'
            values.append(s)
        return self.__class__.__name__ + '(['+ ', '.join(values) +'])'
