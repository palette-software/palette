#!/usr/bin/env python
import os
import tempfile
import shutil
import subprocess
import ConfigParser
import pkg_resources

from webob import exc

from akiri.framework import GenericWSGIApplication

class PostfixException(Exception):
    pass

class Application(GenericWSGIApplication):

    def service_POST(self, req):
        try:
            data = self.post(req)
        except (IOError, PostfixException) as ex:
            print 'error', ex
            return {'error': str(ex)}

        if not 'sasl' in data:
            # Don't leave any old files around.
            self.remove("/etc/postfix/sasl_passwd")
            self.remove("/etc/postfix/sasl_passwd.db")

        # Our caller expects dashes.
        data = {key.replace('_', '-'): value for key, value in data.items()}
        return data

    def remove(self, name):
        try:
            os.unlink(name)
        except (OSError, IOError) as ex:
            pass

    def post(self, req):
        print req.POST

        data = self.getdata(req)   # raises an exception if not sane
        if data['mail_server_type'] == 3: # "None"
            self.run("/usr/sbin/service postfix stop")
            return data

        path = pkg_resources.resource_filename(__name__, 'server.ini')
        if not os.path.exists(path):
            print "does not exist:", path
            raise exc.HTTPInternalServerError()

        parser = ConfigParser.ConfigParser()
        parser.read(path)

        exec_dir = os.path.dirname(os.path.realpath(__file__))
        main_pre_cf_fname = os.path.join(exec_dir,
                                         parser.get('postfix', 'main_pre_cf'))
        main_sasl_cf_fname = os.path.join(exec_dir,
                                        parser.get('postfix', 'main_sasl_cf'))

        # start with pre
        with open(main_pre_cf_fname, 'r') as content_fd:
            main_pre = content_fd.read()

        main_cf = main_pre % data

        # add relay if appropriate
        if data['mail_server_type'] == 2:
            if data['smtp_server']:
                main_cf += "\nrelayhost = [%(smtp_server)s]:%(smtp_port)s" % \
                            data

            # Add sasl portion
            if 'smtp_username' in data and data['smtp_username'] and \
                                                    data['smtp_password']:
                main_cf += '\n'
                with open(main_sasl_cf_fname, 'r') as content_fd:
                    main_sasl = content_fd.read()

                main_cf += main_sasl

                sasl_passwd = ("[%(smtp_server)s]:%(smtp_port)s "
                              "%(smtp_username)s:%(smtp_password)s\n") % \
                               data

                (tfd, temp) = tempfile.mkstemp()
                fd = os.fdopen(tfd, "w")
                fd.write(sasl_passwd)
                fd.close()

                shutil.move(temp, "/etc/postfix/sasl_passwd")
                self.run("/usr/sbin/postmap /etc/postfix/sasl_passwd")
                data['sasl'] = 'yes'

        (tfd, temp) = tempfile.mkstemp()
        fd = os.fdopen(tfd, "w")
        fd.write(main_cf)
        shutil.move(temp, "/etc/postfix/main.cf")

        # Start in case it is stopped (doesn't hurt or fail to start again)
        self.run("/usr/sbin/service postfix start")
        # Reload in case it was already started
        self.run("/usr/sbin/service postfix reload")

        return data

    def getdata(self, req):
        """Check incoming request for validity and if valid, return
           a dictionary with the values in the required format."""

        # We need the keys to be underscore, for variable substitution.
        data = {key.replace('-', '_'): value for key, value in req.POST.items()}

        if not 'mail_server_type' in data:
            raise PostfixException("missing mail-server-type")

        if not data['mail_server_type'].isdigit():
            raise PostfixException(
                    "bad mail-server-type: " + data['mail_server_type'])

        data['mail_server_type'] = int(data['mail_server_type'])


        if data['mail_server_type'] == 3: # "None"
            return data

        if not 'alert_email_address' in data:
            raise PostfixException("missing alert-email-address")

        if data['alert_email_address'].find('@') == -1:
            raise PostfixException("bad email address - missing @<domain>" + \
                                    data['alert_email_address'])

        data['from_email'] = "<" + data['alert_email_address'] + ">"
        if data['alert_email_name']:
            data['from_email'] = data['alert_email_name'] + ' ' + \
                                 data['from_email']

        dstart = data['alert_email_address'].find('@')
        data['mail_domain'] = data['alert_email_address'][dstart+1:]

        if data['mail_server_type'] == 2:
            if not 'smtp_server' in data or not data['smtp_server']:
                raise PostfixException("Missing mail server for relay")

            if not 'smtp_port' in data or not data['smtp_port']:
                raise PostfixException("Missing mail server port for relay")

            if not data['smtp_port'].isdigit():
                raise PostfixException("bad smtp port: " + \
                                                        data['smtp_port'])
            data['smtp_port'] = int(data['smtp_port'])

            if 'smtp_username' in data and not 'smtp_password' in data:
                raise PostfixException(
                            "Must have smtp-password if smtp-username is set.")

        return data

    def run(self, cmd):
        """Raises CalledProcessError if non-zero status"""

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, shell=True)
        (output, _nothing) = process.communicate()
        print "output = ", output
        if process.returncode:
            raise PostfixException("Command '%s' failed: %s" % (cmd, output))

application = Application()

if __name__ == '__main__':
    from akiri.framework.server import runserver

    runserver(application, port=9091, use_reloader=True)
