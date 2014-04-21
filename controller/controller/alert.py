import smtplib
from email.mime.text import MIMEText

class Alert(object):

    def __init__(self, config, log):
        self.config = config
        self.log = log
        self.enabled = config.getboolean('alert', 'enabled', default=False)
        self.to_email = config.get('alert', 'to_email',
                                   default="nobody@nowhere.nohow")
        self.from_email = config.get('alert', 'from_email',
                                     default="alerts@palette-software.com")
        self.smtp_server = config.get('alert', 'smtp_server',
                                    default="localhost")
        self.smtp_port = config.getint("alert", "smtp_port", default=25)

        DEFAULT_ALERT_LEVEL = 1
        self.alert_level = config.getint("alert", "alert_level", default=DEFAULT_ALERT_LEVEL)
        if self.alert_level < 1:
            self.log.err("Invalid alert level: %d, setting to %d",
                                    self.alert_level, DEFAULT_ALERT_LEVEL)
            self.alert_level = DEFAULT_ALERT_LEVEL

    def send(self, subject, body=None):
        """Send an alert.
            Arguments:
                subject:    The subject to send.  If alt_body is not
                            specified, the text is used for both the
                            subject and body.

                body:       If not specified, the subject is also
                            used as the body.
                            If specified, is used as the message body
                            and:.
                                If body is a string, the is used for the
                                message body.
                                If body is a dictionary, it is assumed to
                                be a body from a message reply and it is
                                formatted.
        """

        if not body:
            message = subject
        else:
            message = self.make_message(subject, body)

        if not self.enabled:
            self.log.info(\
                "Alerts disabled.  Not sending: Subject: %s, Message: %s",
                                                            subject, message)
            return

        msg = MIMEText(message)

        msg['Subject'] = "Palette Alert: " + subject
        msg['From'] = self.from_email
        msg['To'] = self.to_email
        msg_str = msg.as_string()

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.sendmail(self.from_email, [self.to_email], msg_str)
            server.quit()
        except (smtplib.SMTPException, EnvironmentError) as e:
            self.log.error("Email send failed, text: %s, exception: %s, server: %s, port: %d",
                message, e, self.smtp_server, self.smtp_port)
            return

        self.log.info("Emailed event: " + message)

        return

    def make_message(self, subject, body):
        """Given the subject and body, return a formatted message, according to
        the alert level.  The higher the alert level, the more details
        the user will receive.
            alert level 1:
                Only 'stderr'.

            alert level 2:
                stderr, stdout, exit status

            alert level 3:
                Everything including XID, run-status, etc.

            Arguments:
                subject  The subject for the alert message.
                body     A string or the 'body' dictionary response
                         from the agent.
        """

        if isinstance(body, str) or isinstance(body, unicode):
            return body

        if type(body) != dict:
            self.log.info("alert was passed a %s instead of string or dictionary.",  type(body))
            return str(body)

        message = subject + '\n\n'

        if self.alert_level < 1:   # too minimal, not even errors included.
            return message
        elif self.alert_level >= 3:
            # Include every key we get, even keys we may not know about:
            for key in sorted(body.keys()):
                message += self.indented(key, body[key], always_include=True)
            return message

        # Reasonable alerts levels here: 1 and 2.
        if body.has_key('error'):
            message += self.indented("Unexpected Error", body['error']) + '\n'

        if body.has_key('info'):
            message += self.indented("Note", body['info']) + '\n'

        # Always include stderr.
        if body.has_key('stderr'):
            message += self.indented('Error', body['stderr'])

        # And include stdout
        if body.has_key('stdout'):
            message += self.indented("Output", body['stdout'])

        if self.alert_level == 2:
            # Add a bit more for level 2.
            if body.has_key("xid"):
                message += "XID: %d\n" % body['xid']
            if body.has_key("exit-status"):
                message += "Exit status: %d\n" % body['exit-status']

        return message

    def indented(self, section, value, always_include=False):
        """Take the input section title/name, and value argument, split
            it into lines, and return a string with the section name,
            then all lines, indented.

            If the value is empty, don't return the section or value.

            Arguments:
                section:  The name of the section, like "Errors" or "Output".

                value:   An integer or string.  If it is a string, it
                         could potentially have many newlines in it that
                         will be split up and indented.

                always_include: If False (default), don't include if
                                value is an empty string.
                                If True, include even if the a value
                                is an empty string.
            """

        if type(value) == int:
            return "%s: %d\n" % (section, value)

        if not value and not always_include:
            # If the string is empty, ignore it unless always_include is set.
            return ""

        lines = section + ':' + "\n"
        for line in value.split("\n"):
            lines += "    " + line + "\n"

        return lines

if __name__ == "__main__":
    import logging
    from config import Config

    config = Config("../DEBIAN/etc/controller.ini")

    handler = logging.StreamHandler()

    DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    DEFAULT_FORMAT = '[%(asctime)s] %(levelname)s %(message)s'
    formatter = logging.Formatter(fmt=DEFAULT_FORMAT, datefmt=DEFAULT_DATE_FORMAT)

    log = logging.getLogger("main")

    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)

    log.info("alert test starting")

    alert = Alert(config, log)
    alert.send("Test Alert")
