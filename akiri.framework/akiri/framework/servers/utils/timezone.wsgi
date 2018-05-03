#!/usr/bin/env python
import os
import subprocess
from pytz import common_timezones as timezones
from akiri.framework import GenericWSGIApplication

class TZException(Exception):
    pass


class Application(GenericWSGIApplication):

    def service_POST(self, req):
        try:
            data = self.post(req)
        except (IOError, TZException) as ex:
            print 'error', ex
            return {'error': str(ex)}

        return data

    def remove(self, name):
        try:
            os.unlink(name)
        except (OSError, IOError) as ex:
            pass

    def post(self, req):
        print "req", req.POST
        data = req.POST.mixed()

        if 'timezone' not in data or not data['timezone']:
            raise TZException("Missing timezone")

        timezone = data['timezone']
        if timezone not in timezones:
            raise TZException("Invalid timezone: " + str(timezone))

        # Updating the timezone with timedatectl requires permissive SELinux policy
        # allow systemd_timedated_t initrc_t:dbus send_msg;
        self.run('mv /etc/localtime /etc/localtime.bak')
        self.run('ln -s /usr/share/zoneinfo/{} /etc/localtime'.format(timezone))
        self.run('/bin/systemctl restart ntpd')

        return data

    def run(self, cmd):
        """Raises CalledProcessError if non-zero status"""

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, shell=True)
        (output, _nothing) = process.communicate()
        print "output = ", output
        if process.returncode:
            raise TZException("Command '%s' failed: %s" % (cmd, output))


application = Application()

if __name__ == '__main__':
    from akiri.framework.server import runserver

    runserver(application, port=9093, use_reloader=True)
