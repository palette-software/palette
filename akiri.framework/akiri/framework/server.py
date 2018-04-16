# Copyright (c) Akiri Solutions, Inc.  All Rights Reserved.
"""
Server functionality.
"""
import paste.httpserver

def runserver(application, **kwargs):
    """
    Indefinitely run a webserver using the paste.httpserver.serve()
    options + plus 'use_reloader'.  Adding more watch files must be done
    explicitly.
    """
    if 'use_reloader' in kwargs and kwargs['use_reloader']:
        del kwargs['use_reloader']
        from .reloader import install
        install()

    return paste.httpserver.serve(application, **kwargs)
