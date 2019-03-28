import logging


class ExtraHeadersMiddleware():
    """
    headers:
        The extra headers to add in the same format as for the WSGI
        start_response() function

    logger:
        a python.logging compatible logger

    statuses:
        A list of status codes that will trigger the addition of the extra
        headers.  If set to None, all requests will have the headers added.
    """
    def __init__(self, app,
                 headers=[],
                 statuses=[200],
                 logger=logging):
        self._app = app
        self._headers = headers
        self._logger = logger
        self._statuses = map(lambda s: str(s), statuses)
        self._log(logging.INFO,
                "statuses: %s",
                self._statuses)

    def __call__(self, env, start_response):

        # Our fake start_response function
        def fake_start_response(status, headers, exc_info=None):

            # add our extra headers
            if self._should_add_headers(status):
                self._log(logging.INFO,
                          "Status = %s => Adding extra headers: %s",
                          status,
                          self._headers)
                headers += self._headers

            return start_response(status, headers, exc_info)

        return self._app(env, fake_start_response)


    def _log(self, lvl, msg, *args, **kwargs):
        if self._logger:
            self._logger.log(lvl, msg, *args, **kwargs)

    # Is this response an OK response (do we need to add our extra headers)
    def _should_add_headers(self, status):
        return status[0:3] in self._statuses

