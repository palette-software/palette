import logging
import datetime
import Cookie




## MIDDLEWARE

class CsrfMiddleware():
    """ Generic middleware to add / check CSRF tokens in WSGI apps.

    The generation and validation of tokens are handled by two user-provided functions
    `createTokenFn` and `validateTokenFn`.
    """


    def __init__(self, app,
                 createTokenFn,
                 validateTokenFn,
                 tokenCookieName="PaletteCsrfToken",
                 logger=logging):
        """ Creates a new CSRF middleware.

        app:
            The WSGI app to overlay this middleware over

        createTokenFn:
            A function with a signature `(currentTime:DateTime) => token:String`
            that generates a new token that can be validated later using
            `validateTokenFn(token, currentTime)`

        validateTokenFn:
            A function with the signature `(token:String, currentTime: DateTime) => Bool`
            that return True if `token` is valid at `currentTime`.
            The no-replay guarantee requires this function to remove the token
            from the list of valid ones after a single use

        tokenCookieName:
            The name of the Cookie that will be used to store the CSRF token

        logger:
            A python logging compatible logger that will be used for all log messages.
        """
        # Check the args
        if createTokenFn is None:
            raise ArgumentError("createTokenFn must be a function")

        if validateTokenFn is None:
            raise ArgumentError("validateTokenFn must be a function")


        self._app = app
        self._logger = logger
        self._tokenCookieName = tokenCookieName
        # Save the Fns
        self._createTokenFn = createTokenFn
        self._validateTokenFn = validateTokenFn
        # boot
        self._log(logging.INFO, "Initializing CSRF middleware")


    def __call__(self, env, start_response):


        # Get the current time so we can save the token with an expiration
        currentTime = datetime.datetime.now()

        # Fetch the current time
        existing_cookie = self._getCookie(env)


        if self._shouldCheckForCookie(env):

            # Fail if cookie is not present
            if existing_cookie is None:
                return self._send_csrf_failiure_response(start_response)

            # Fail if token check fails
            if not self._validateTokenFn(existing_cookie, currentTime):
                return self._send_csrf_failiure_response(start_response)



        # Our fake start_response function
        def fake_start_response(status, headers):
            """ Adds a Set-Cookie header with a new CSRF token to the response """

            # Get the current time so we can save the token with an expiration
            currentTime = datetime.datetime.now()

            # Generate a new token
            token = self._createTokenFn(existing_cookie, currentTime)

            # Cookie-fy the token and set it
            session_cookie = Cookie.SimpleCookie()
            session_cookie[self._tokenCookieName] = token

            # Generate cookie headers
            headers.extend(("Set-Cookie", morsel.OutputString())
                            for morsel
                            in session_cookie.values())

            return start_response(status, headers)

        return self._app(env, fake_start_response)


    def _send_csrf_failiure_response(self, start_response):
        """ Starts an HTTP response signaling CSRF failiure """
        response_text = """
            <h1>CSRF error</h1>
        """
        start_response("400 CSRF error", [('Content-type', 'text/html'),
                                          ('Content-Length', str(len(response_text)))])
        return [response_text]


    def _shouldCheckForCookie(self, env):
        """ Returns True if the CSRF cookie should be checked for this request """
        return env['REQUEST_METHOD'] in ['POST', 'PUT']


    def _getCookie(self, env):
        """ Attempts to return the CSRF token cookie or None if CSRF cookie is not set """
        self._log(logging.INFO, "Checking for CSRF cookie '%s'", self._tokenCookieName)
        # If no cookies present, then the token is None
        if 'HTTP_COOKIE' not in env:
            return None

        # Parse the cookies by using Cookie.SimpleCookie()
        c = Cookie.SimpleCookie()
        c.load(env["HTTP_COOKIE"])

        # If no cookie then no cookie
        if not self._tokenCookieName in c:
            return None

        # extract the cookie value
        return c[self._tokenCookieName].value


    def _log(self, lvl, msg, *args, **kwargs):
        """ Attempts to call the logger (if provided) by forwarding all args """
        if self._logger:
            self._logger.log(lvl, msg, *args, **kwargs)

