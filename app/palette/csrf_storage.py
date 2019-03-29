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



def format_sql(format_string, *args):
    """ Format an SQL string and escape things """
    def escape(val):
        if isinstance(val, basestring):
            # TODO: escape to prevent SQL injection attack with a funky token string
            return val
        elif isinstance(val, numbers.Number):
            return str(val)
        elif isinstance(val, datetime.datetime):
            return val.isoformat()

        raise TypeError("Cannot SQL escape value: %s" % (val))

    # escape all arguments
    escaped_args = map(escape, args)
    return format_string.format(*escaped_args)





class SqlBackedComponent(LoggingComponent):
    """ Base class for components using an underlying PostgresSQL connection """

    def __init__(self,
                 connectionFn=None,
                 table_name="palette_csrf_tokens",
                 logger=logging.getLogger('sql-data-source')):
        LoggingComponent.__init__(self, logger)
        self.table_name = table_name
        self._connectionFn = connectionFn

        self._create_table()

    def _create_table(self):
        """ Attempts to create the table if it does not exist in PostgreSQL.

        This method will call self._table_sql() to get the table columns of the SQL statement.
        """
        # Create the table creation statement
        table_inner = self._table_sql()
        # No escaping, lets hope the developer is not crazy...
        sql = "CREATE TABLE IF NOT EXISTS {0} ({1})".format(
            self.table_name, table_inner)

        # Run the statement
        self.run_sql(sql)



    def run_sql(self, sql_string, *args):
        """ Attempts to run the SQL statement if a connection is available """
        sql = format_sql(sql_string, *args)

        self.log(logging.DEBUG, "run_sql(): %s", sql)

        if self._connectionFn is None:
            self.log(logging.INFO, "No SqlAlchemy connection function - cannot use backing store")
            return None

        connection = self._connectionFn()

        if self._connectionFn is None:
            self.log(logging.ERROR, "SqlAlchemy connection function returned None - cannot use backing store")
            return None

        return connection.execute(sql)


    def run_single_value(self, defaultValue, sql_string, *args):
        """ Attempts to run an SQL statement that results in a single value and return that value.

        defaultValue:
            The default value to return if the statement yields no results
        """
        value = defaultValue
        for row in self.run_sql(sql_string, *args):
            value = row[0]

        self.log(logging.DEBUG, "RETURN VALUE = %s", value)
        return value


    def _table_sql(self):
        """ The table columns for the table defition to be created """
        raise NotImplementedError("SqlCsrfStorage::_table_sql() not implemented")




class SqlCsrfStorage(SqlBackedComponent):
    """ Generic store for CSRF tokens implemented on top of SqlAlchemy / PostgreSQL """

    def __init__(self,
                 connectionFn=None,
                 table_name="palette_csrf_tokens",
                 logger=logging.getLogger('sql-csrf-storage')):
        SqlBackedComponent.__init__(self, connectionFn, table_name=table_name, logger=logger)


    def create_token(self, old_token, current_time):
        """ Implementation for createToken """

        def generate_new_token():
            token = generate_token()

            self.run_sql("INSERT INTO {0} (token_str, expires_at) VALUES ('{1}', '{2}')",
                         self.table_name, token, current_time)
            return token

        def delete_old_token():
            if old_token is None:
                return

            self.run_sql("DELETE FROM {0} WHERE token_str='{1}'",
                         self.table_name, old_token)


        delete_old_token()
        return generate_new_token()


    def validate_token(self, token, current_time):
        """ Validate a token by checking it in the DB """

        token_count =  self.run_single_value(0, "SELECT COUNT(1) FROM {0} WHERE token_str = '{1}'",
                                             self.table_name, token)

        return token_count > 0


    def _table_sql(self):
        """ The table columns for the table defition to be created """
        return """
            token_str VARCHAR(64) NOT NULL PRIMARY KEY,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL
        """





class UserLockoutStorage(SqlBackedComponent):
    """ Generic store for User login attempts implemented on top of SqlAlchemy / PostgreSQL """

    def __init__(self,
                 connectionFn=None,
                 table_name="palette_user_lockout",
                 logger=logging.getLogger('sql-csrf-storage'),
                 max_attempts=5):
        SqlBackedComponent.__init__(self, connectionFn, table_name=table_name, logger=logger)
        self.max_attempts = max_attempts


    def successful_attempt(self, user_name):
        """ Clears the record of the users failed login attempts after a successful login """
        self.run_sql("DELETE FROM {0} WHERE user_name = '{1}'", self.table_name, user_name)

    def failed_attempt(self, user_name):
        """ Increments the failed attempt counter for the user """

        # Check if we have the user

        attempt_count =  self._get_attempt_count(user_name)

        if attempt_count > 0:
            self.run_sql("UPDATE {0} SET attempt_count={1} WHERE user_name='{2}'",
                         self.table_name, attempt_count + 1, user_name)
        else:
            # Create a new record
            self.run_sql("INSERT INTO {0} (user_name, attempt_count) VALUES ('{1}', 1)",
                         self.table_name, user_name)



    def is_user_locked_out(self, user_name):
        """ Returns True if the user is locked out because of too many login attempts """
        return self._get_attempt_count(user_name) > self.max_attempts


    def _get_attempt_count(self, user_name):
        """ Returns the number of attempts the user has tried to login unsuccesfully (since they were last cleared) """
        return self.run_single_value(0, "SELECT attempt_count FROM {0} WHERE user_name = '{1}'",
                                     self.table_name, user_name)


    def _table_sql(self):
        """ The table columns for the table defition to be created """
        return """
            user_name VARCHAR(64) NOT NULL PRIMARY KEY,
            attempt_count INT NOT NULL
        """


class EmptyUserLockoutStorage():
    """ Interface to implement for User Lockout backing storage """

    def successful_attempt(self, user_name):
        """ Clears the record of the users failed login attempts after a successful login """
        raise NotImplementedError("successful_attempt() not implemented")

    def failed_attempt(self, user_name):
        """ Increments the failed attempt counter for the user """
        raise NotImplementedError("failed_attempt() not implemented")

    def is_user_locked_out(self, user_name):
        """ Returns True if the user is locked out because of too many login attempts """
        raise NotImplementedError("is_user_locked_out() not implemented")


# TODO: move this import
from cgi import parse_qs

def parse_request_body(env):
    try:
        # CONTENT_LENGTH may be empty or missing
        request_body_size = int(env.get('CONTENT_LENGTH', 0))

        print "Content-length={}".format(request_body_size)
        # Read the request body
        request_body = env['wsgi.input'].read(request_body_size)
        print "Body={}".format(request_body)
        # Attempt to parse the request body as query string
        return parse_qs(request_body)
    except ValueError:
        # No body is present, or not in query-string format
        # so we return an empty
        return {}


class UserLockoutMiddleware(LoggingComponent):
    def __init__(self, app,
                 storage=EmptyUserLockoutStorage(),
                 logger=logging,
                 user_name_param='username'):
        """ Creates a new CSRF middleware.

        app:
            The WSGI app to overlay this middleware over

        storage:
            The underlying storage to use (see EmptyCsrfStorage for details)

        token_cookie_name:
            The name of the Cookie that will be used to store the CSRF token

        logger:
            A python logging compatible logger that will be used for all log messages.
        """
        self._app = app
        self._logger = logger
        self._storage = storage
        self._user_name_param = user_name_param
        # boot
        self.log(logging.INFO, "Initializing User Lockout middleware")


    def __call__(self, env, start_response):

        # Short-circuit if we aren't intersted
        if not self._should_check_request(env):
            return self._app(env, start_response)


        # Attempt to parse the POST params
        post_params = parse_request_body(env)


        # Fail if no username provided
        if self._user_name_param not in post_params:
            return self._send_no_user_name_found(start_response)

        # Extract the username (parse_qs returns an array for each
        # key, so we take the first element, and hope that parse_qs
        # is not buggy and will never give us zero-length arrays)
        user_name = post_params[self._user_name_param][0]

        # If locked out reply with the lockout message
        if self._storage.is_user_locked_out(user_name):
            return self._send_lockout_response(start_response)


        def fake_start_response(status, headers, exc_info=None):

            # Update the storage based on the success / failiure of the login attempt
            if self._is_successful_login(status):
                self._storage.successful_attempt(user_name)
            else:
                self._storage.failed_attempt(user_name)

            # keep on truckin'
            return start_response(status, headers, exc_info)

        return self._app(env, fake_start_response)


    def _send_no_user_name_found(self, start_response):
        return self._send_text(start_response, "400 No user name", "<h1>Cannot find user name</h1>")

    def _send_lockout_response(self, start_response):
        """ Starts an HTTP response signaling user lockout """
        return self._send_text(start_response, "400 User locked out", "<h1>User locked out</h1>")


    def _send_text(self, start_response, status, response_text):
        """ Starts an HTTP response signaling user lockout """
        start_response(status, [('Content-type', 'text/html'),
                                               ('Content-Length', str(len(response_text)))])
        return [response_text]


    def _should_check_request(self, env):
        """ Returns True if the user needs to be checked for this request """
        # We are only checking POST requests
        return env['REQUEST_METHOD'] in ['POST']


    def _is_successful_login(self, status):
        """ Returns True if the login request was successful """
        # Palette Center returns NOT 200 on login failiure (should be FORBIDDEN,
        # but checking against 200 / 204 should be safer)
        return status[0:3] in ['200', '204']

