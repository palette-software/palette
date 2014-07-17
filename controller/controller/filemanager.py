import os
import httplib
import urllib

import exc

class FileManager(object):

    def __init__(self, agent):
        self.server = agent.server
        self.agent = agent

    def uri(self, path):
        return '/file?path=' + urllib.quote_plus(path)

    def checkpath(self, path):
        if path.endswith('/') or path.endswith('\\'):
            raise ValueError("'path' may not refer to a directory")

    def get(self, path):
        self.checkpath(path)
        uri = self.uri(path)
        self.server.log.debug("FileManager GET %s", uri)
        return self.agent.http_send('GET', uri)

    def save(self, path, target='.'):
        """Retrieves a remote file and saves it locally."""
        target = os.path.abspath(os.path.expanduser(target))
        self.checkpath(path)

        if os.path.isdir(target):
            target = os.path.join(target, self.agent.path.basename(path))

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
        return self.agent.connection.http_send('PUT', uri, data)

    def sha256(self, path):
        data = {'action':'SHA256', 'path':path}
        body = self.agent.connection.http_send_json('/file', data)
        return json.loads(body)

    def move(self, src, dst):
        data = {'action':'MOVE', 'source':src, 'destination':dst}
        body = self.agent.connection.http_send_json('/file', data)
        return json.loads(body)

    def listdir(self, path):
        data = {'action':'LISTDIR', 'path':path}
        body = self.agent.connection.http_send_json('/file', data)
        return json.loads(body)

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
        return self.agent.http_send('DELETE', uri)
