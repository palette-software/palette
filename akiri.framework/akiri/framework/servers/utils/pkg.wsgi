#!/usr/bin/env python

from akiri.framework.servers.pkg import PkgApp
application = PkgApp()

if __name__ == '__main__':
    from akiri.framework.server import loadserver

    server = loadserver()
    server.serve_forever(application)
