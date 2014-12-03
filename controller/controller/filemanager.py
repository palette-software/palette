import os
import urllib
import json
import exc
import httplib

class FileManager(object):

    def __init__(self, agent):
        self.server = agent.server
        self.agent = agent

    def uri(self, path):
        return '/file?path=' + urllib.quote_plus(path)

    def checkpath(self, path):
        if path.endswith('/') or path.endswith('\\'):
            raise IOError("'path' may not refer to a directory")

    def get(self, path):
        try:
            self.checkpath(path)
            uri = self.uri(path)
            self.server.log.debug("FileManager GET %s", uri)
            return self.agent.connection.http_send('GET', uri)
        except (exc.HTTPException, httplib.HTTPException,
                EnvironmentError) as ex:
            raise IOError("filemanager.get failed: %s" % str(ex))

    def save(self, path, target='.'):
        """Retrieves a remote file and saves it locally."""
        target = os.path.abspath(os.path.expanduser(target))
        self.checkpath(path)

        if os.path.isdir(target):
            target = os.path.join(target, self.agent.path.basename(path))

        try:
            with open(target, "w") as f:
                data = self.get(path)
                f.write(self.get(path))
            return {
                'target': target,
                'path': path,
                'size': len(data)
                }
        except (exc.HTTPException, httplib.HTTPException,
                EnvironmentError) as ex:
            raise IOError("filemanager.save failed: %s" % str(ex))

    def put(self, path, data):
        self.checkpath(path)
        uri = self.uri(path)
        headers = {}
        if not data:
            # http://bugs.python.org/issue14721
            headers['content-length'] = 0
        self.server.log.debug("FileManager PUT %s: %d", uri, len(data))
        try:
            body = self.agent.connection.http_send('PUT', uri, data,
                                                   headers=headers)
            if body:
                return json.loads(body)
            else:
                return {}
        except (exc.HTTPException, httplib.HTTPException,
                EnvironmentError) as ex:
            raise IOError("filemanager.put failed: %s" % str(ex))

    def sha256(self, path):
        data = {'action':'SHA256', 'path':path}
        try:
            body = self.agent.connection.http_send_json('/file', data)
            return json.loads(body)
        except (exc.HTTPException, httplib.HTTPException,
                EnvironmentError, ValueError) as ex:
            raise IOError("filemanager.sha256 failed: %s" % str(ex))

    def move(self, src, dst):
        data = {'action':'MOVE', 'source':src, 'destination':dst}
        try:
            body = self.agent.connection.http_send_json('/file', data)
            return json.loads(body)
        except (exc.HTTPException, httplib.HTTPException,
                EnvironmentError, ValueError) as ex:
            raise IOError("filemanager.move failed: %s" % str(ex))

    def listdir(self, path):
        data = {'action':'LISTDIR', 'path':path}
        try:
            body = self.agent.connection.http_send_json('/file', data)
            return json.loads(body)
        except (exc.HTTPException, httplib.HTTPException,
                EnvironmentError, ValueError) as ex:
            raise IOError("filemanager.listdir failed: %s" % str(ex))

    def mkdirs(self, path):
        data = {'action':'MKDIRS', 'path':path}
        try:
            body = self.agent.connection.http_send_json('/file', data)
            return json.loads(body)
        except (exc.HTTPException, httplib.HTTPException,
                EnvironmentError, ValueError) as ex:
            raise IOError("filemanager.mkdirs failed: %s" % str(ex))

    def filesize(self, path):
        data = {'action':'FILESIZE', 'path':path}
        try:
            body = self.agent.connection.http_send_json('/file', data)
            return json.loads(body)
        except (exc.HTTPException, httplib.HTTPException,
                EnvironmentError, ValueError) as ex:
            raise IOError("filemanager.mkdirs failed: %s" % str(ex))

    def sendfile(self, path, source):
        source = os.path.abspath(os.path.expanduser(source))
        with open(source, "rb") as f:
            data = f.read()
            body = self.put(path, data)
        self.server.log.debug("sendfile source '%s' path '%s' size %d." % \
                                                    (source, path, len(data)))
        body['source'] = source
        body['path'] = path
        body['size'] = len(data)
        return body

    def delete(self, path):
        self.checkpath(path)
        uri = self.uri(path)
        self.server.log.debug("FileManager DELETE %s", uri)
        try:
            body = self.agent.connection.http_send('DELETE', uri)
            return json.loads(body)
        except (exc.HTTPException, httplib.HTTPException,
                EnvironmentError) as ex:
            raise IOError("filemanager.delete failed: %s" % str(ex))
