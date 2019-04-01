import logging
import datetime
import Cookie


class EmptyCsrfStorage():
    """ Interface to implement for CSRF backing storage """
    def create_token(self, old_token, current_time):
        """ A function with a signature `(current_time:DateTime) => token:String`

            that generates a new token that can be validated later using
            `validateTokenFn(token, current_time)`
        """
        raise NotImplementedError("createToken() not implemented")

    def validate_token(self, token, current_time):
        """
            A function with the signature `(token:String, current_time: DateTime) => Bool`

            that return True if `token` is valid at `current_time`.
            The no-replay guarantee requires this function to remove the token
            from the list of valid ones after a single use
        """
        raise NotImplementedError("validateToken() not implemented")



## MIDDLEWARE

class CsrfMiddleware():
    """ Generic middleware to add / check CSRF tokens in WSGI apps.

    The generation and validation of tokens are handled by two user-provided functions
    `createTokenFn` and `validateTokenFn`.
    """


    def __init__(self, app,
                 storage=EmptyCsrfStorage(),
                 token_cookie_name="PaletteCsrfToken",
                 logger=logging):
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
        self._token_cookie_name = token_cookie_name
        # Save the Fns
        self._storage = storage
        # boot
        self.log(logging.INFO, "Initializing CSRF middleware")


    def __call__(self, env, start_response):


        # Get the current time so we can save the token with an expiration
        current_time = datetime.datetime.now()

        # Fetch the current time
        existing_token = self._get_cookie(env)


        if self._should_check_for_cookie(env):

            # Fail if cookie is not present
            if existing_token is None:
                return self._send_csrf_failiure_response(start_response)

            # Fail if token check fails
            if not self._storage.validate_token(existing_token, current_time):
                return self._send_csrf_failiure_response(start_response)



        # Our fake start_response function
        def fake_start_response(status, headers, exc_info=None):
            """ Adds a Set-Cookie header with a new CSRF token to the response """

            # Get the current time so we can save the token with an expiration
            current_time = datetime.datetime.now()

            self.log(logging.INFO, "existing CSRF token = '%s'", existing_token)

            # Generate a new token
            token = self._storage.create_token(existing_token, current_time)

            # Cookie-fy the token and set it
            session_cookie = Cookie.SimpleCookie()
            session_cookie[self._token_cookie_name] = token

            # Generate cookie headers
            headers.extend(("Set-Cookie", morsel.OutputString())
                            for morsel
                            in session_cookie.values())

            return start_response(status, headers, exc_info)

        return self._app(env, fake_start_response)


    def _send_csrf_failiure_response(self, start_response):
        """ Starts an HTTP response signaling CSRF failiure """
        response_text = """
            <h1>CSRF error</h1>
        """
        start_response("400 CSRF error", [('Content-type', 'text/html'),
                                          ('Content-Length', str(len(response_text)))])
        return [response_text]


    def _should_check_for_cookie(self, env):
        """ Returns True if the CSRF cookie should be checked for this request """
        return env['REQUEST_METHOD'] in ['POST', 'PUT']


    def _get_cookie(self, env):
        """ Attempts to return the CSRF token cookie or None if CSRF cookie is not set """
        # If no cookies present, then the token is None
        if 'HTTP_COOKIE' not in env:
            return None

        # Parse the cookies by using Cookie.SimpleCookie()
        c = Cookie.SimpleCookie()
        c.load(env["HTTP_COOKIE"])

        # If no cookie then no cookie
        if not self._token_cookie_name in c:
            return None

        # extract the cookie value
        return c[self._token_cookie_name].value


    def log(self, lvl, msg, *args, **kwargs):
        """ Attempts to call the logger (if provided) by forwarding all args """
        if self._logger:
            self._logger.log(lvl, msg, *args, **kwargs)

