import os
import httplib
import urllib
import ntpath

import exc

class FileManager(object):

    def __init__(self, agent):
        self.server = agent.server
        self.agent = agent

    def uri(self, path):
        return '/file?path=' + urllib.quote_plus(path)

    def httpexc(self, res, method='GET', body=None):
        if body is None:
            body = res.read()
        raise exc.HTTPException(res.status, res.reason,
                                method=method, body=body)

    def checkpath(self, path):
        if path.endswith('/') or path.endswith('\\'):
            raise ValueError("'path' may not refer to a directory")

    def get(self, path):
        self.checkpath(path)
        uri = self.uri(path)
        self.server.log.debug("FileManager GET %s", uri)
        res = self.agent.http_send('GET', uri)
        if res.status != httplib.OK:
            self.httpexc(res)
        return res.read()

    def save(self, path, target='.'):
        """Retrieves a remote file and saves it locally."""
        target = os.path.abspath(os.path.expanduser(target))
        self.checkpath(path)

        if os.path.isdir(target):
            target = os.path.join(target, ntpath.basename(path))

        with open(target, "w") as f:
            data = self.get(path)
            f.write(self.get(path))
        return {
            'target': target,
            'path': path,
            'size': len(data)
            }

    def put(self, path, data):
        self.checkpath(path)
        uri = self.uri(path)
        self.server.log.debug("FileManager PUT %s: %s", uri, data)
        res = self.agent.http_send('PUT', uri, data)
        if res.status != httplib.OK:
            self.httpexc(res, method='PUT')

    def sendfile(self, path, source):
        source = os.path.abspath(os.path.expanduser(source))
        with open(source, "r") as f:
            data = f.read()
            self.put(path, data)
        return {
            'source': source,
            'path': path,
            'size': len(data)
            }

    def delete(self, path):
        self.checkpath(path)
        uri = self.uri(path)
        self.server.log.debug("FileManager DELETE %s", uri)
        res = self.agent.http_send('DELETE', uri)
        if res.status != httplib.OK:
            self.httpexc(res, method='DELETE')
