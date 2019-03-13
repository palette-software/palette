import logging
import uuid
import threading
import numbers
import datetime


def generate_token():
    """ Generates a new token """
    return str(uuid.uuid1())


class LoggingComponent():
    """ Generic class with an injected logger and a log() method """
    def __init__(self, logger):
        self._logger = logger

    def log(self, lvl, msg, *args, **kwargs):
        """ Attempts to call the logger (if provided) by forwarding all args """
        if self._logger:
            self._logger.log(lvl, msg, *args, **kwargs)



class InMemoryCsrfStorage(LoggingComponent):
    """ An implementation of an in-memory dictionary used for CSRF storage """
    def __init__(self,
                 logger=logging.getLogger('in_memory_csrf_storage')):
        LoggingComponent.__init__(self, logger)
        # Our token storage
        self._tokens = {}
        # Create a lock to protect the tokens dict
        self._lock = threading.Lock()

    def create_token(self, old_token, current_time):
        token = generate_token()

        # Ensure locking
        with self._lock:
            # remove old token
            if old_token is not None and old_token in self._tokens:
                self.log(logging.DEBUG, "deleting old token: %s", old_token)
                del self._tokens[old_token]

            # update new token
            self.log(logging.DEBUG, "saving new token: %s", token)
            self._tokens[token] = current_time
            return token

    def validate_token(self, token, current_time):
        self.log(logging.DEBUG, "validating token: %s", token)
        with self._lock:
            return token in self._tokens



def format_sql(str, *args):
    """ Format an SQL string and escape things """
    def escape(val):
        if isinstance(val, basestring):
            return "%s" % val
        elif isinstance(val, numbers.Number):
            return str(val)
        elif isinstance(val, datetime.datetime):
            return val.isoformat()

        raise TypeError("Cannot SQL escape value: %s" % (val))

    # escape all arguments
    escaped_args = map(escape, args)
    return str.format(*escaped_args)



class SqlCsrfStorage(LoggingComponent):
    """ Generic store for CSRF tokens implemented on top of SqlAlchemy / PostgreSQL """

    def __init__(self,
                 connectionFn=None,
                 table_name="palette_csrf_tokens",
                 logger=logging.getLogger('sql-csrf-storage')):
        LoggingComponent.__init__(self, logger)
        self.table_name = table_name
        self._connectionFn = connectionFn

        self._create_table()


    def create_token(self, old_token, current_time):
        """ Implementation for createToken """

        def generate_new_token():
            token = generate_token()

            sql = format_sql("INSERT INTO {0} (token_str, expires_at) VALUES ('{1}', '{2}')",
                             self.table_name, token, current_time)

            self._run_sql(sql)
            return token

        def delete_old_token():
            if old_token is None:
                return

            sql = format_sql("DELETE FROM {0} WHERE token_str='{1}'",
                             self.table_name, old_token)
            self._run_sql(sql)


        delete_old_token()
        return generate_new_token()


    def validate_token(self, token, current_time):
        """ Validate a token by checking it in the DB """
        sql = format_sql("SELECT COUNT(1) FROM {0} WHERE token_str = '{1}'",
                         self.table_name, token)

        count = 0
        for row in self._run_sql(sql):
            count = row[0]

        return count > 0


    def _create_table(self):
        """ Attempts to create the table if it does not exist in PostgreSQL """
        # Create the table creation statement
        sql = """
        CREATE TABLE IF NOT EXISTS %s (
            token_str VARCHAR(64) NOT NULL PRIMARY KEY,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL
        )
        """ % (self.table_name)

        # Run the statement
        self._run_sql(sql)

    def _run_sql(self, sql):
        """ Attempts to run the SQL statement if a connection is available """
        self.log(logging.DEBUG, "_run_sql(): %s", sql)

        if self._connectionFn is None:
            self.log(logging.INFO, "No SqlAlchemy connection function - cannot use backing store")
            return None

        connection = self._connectionFn()

        if self._connectionFn is None:
            self.log(logging.ERROR, "SqlAlchemy connection function returned None - cannot use backing store")
            return None

        return connection.execute(sql)


