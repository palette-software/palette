#!/usr/bin/env python
import os
import tempfile
import shutil
import subprocess
import ConfigParser
import pkg_resources

from webob import exc

from akiri.framework import GenericWSGIApplication

class SSLException(Exception):
    pass

class Application(GenericWSGIApplication):

    def service_POST(self, req):
        try:
            data = self.post(req)
        except (IOError, SSLException) as ex:
            print 'error', ex
            return {'error': str(ex)}

        return data

    def remove(self, name):
        try:
            os.unlink(name)
        except (OSError, IOError) as ex:
            pass

    def post(self, req):
        data = self.getdata(req)   # raises an exception if not sane

        if data['enable-ssl'] == 'false':
            return data

        fd = open("/etc/ssl/certs/server.crt", "w")
        fd.write(data['ssl-certificate-file'])
        fd.write('\n')
        fd.close()

        fd = open("/etc/ssl/private/server.key", "w", 0600)
        fd.write(data['ssl-certificate-key-file'])
        fd.write('\n')
        fd.close()

        APACHE_CONFIG_FILE = "/etc/apache2/sites-available/" + \
                             "palette-software-ssl.conf"

        CHAIN_FILE = "/etc/ssl/certs/server-ca.crt"

        if 'ssl-certificate-chain-file' in data and \
                                        data['ssl-certificate-chain-file']:
            fd = open(CHAIN_FILE, "w")
            fd.write(data['ssl-certificate-chain-file'])
            fd.write('\n')
            fd.close()

            # Make sure the chain file is enabled in the conf file.
            self.run("sed --in-place " + \
                "'s@.*SSLCertificateChainFile /@" + \
                "    SSLCertificateChainFile /@'" + \
                " " + APACHE_CONFIG_FILE)
        else:
            # Make sure the chain file is disabled in the conf file.
            self.run("sed --in-place " + \
                "'s@.*SSLCertificateChainFile /@" + \
                "    #SSLCertificateChainFile /@'" + \
                " " + APACHE_CONFIG_FILE)
            # Don't leave any old chain files around.
            self.remove(CHAIN_FILE)

        self.run("/usr/sbin/service apache2 reload")

        return data

    def getdata(self, req):

        """Check the incoming request for validity and if valid, return
           a dictionary with the values in the required format."""

        data = req.POST.mixed()
        if not 'enable-ssl' in data:
            raise SSLException("Missing enable-ssl")

        if data['enable-ssl'] == 'false':
            # No more sanity checking needed.
            return data

        if not 'ssl-certificate-file' in data or \
                                    not data['ssl-certificate-file']:
            raise SSLException("Missing ssl-certificate-file")

        if not 'ssl-certificate-key-file' in data or \
                                not data['ssl-certificate-key-file']:
            raise SSLException("Missing ssl-certificate-key-file")

        return data

    def run(self, cmd):
        """Raises CalledProcessError if non-zero status"""

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, shell=True)
        (output, _nothing) = process.communicate()
        print "output = ", output
        if process.returncode:
            raise SSLException("Command '%s' failed: %s" % (cmd, output))

application = Application()

if __name__ == '__main__':
    from akiri.framework.server import runserver

    runserver(application, port=9092, use_reloader=True)
