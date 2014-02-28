from akiri.framework.wsgi import make_wsgi

path = '/etc/palette.ini'
application = make_wsgi(path)
