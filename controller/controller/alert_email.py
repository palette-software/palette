import smtplib
from email.mime.text import MIMEText

from akiri.framework.ext.sqlalchemy import meta
from sqlalchemy.orm.exc import NoResultFound

from profile import UserProfile

from mako.template import Template
from mako import exceptions
import mako.runtime
mako.runtime.UNDEFINED="*UNDEFINED*"

from event_control import EventControl

class AlertEmail(object):

    def __init__(self, server):
        self.config = server.config
        self.log = server.log
        self.enabled = self.config.getboolean('alert', 'enabled', default=False)
        self.from_email = self.config.get('alert', 'from_email',
                                     default="alerts@palette-software.com")
        self.smtp_server = self.config.get('alert', 'smtp_server',
                                    default="localhost")
        self.smtp_port = self.config.getint("alert", "smtp_port", default=25)

        DEFAULT_ALERT_LEVEL = 1
        self.alert_level = self.config.getint("alert", "alert_level",
                                                        default=DEFAULT_ALERT_LEVEL)

        DEFAULT_MAX_SUBJECT_LEN = 100
        self.max_subject_len = self.config.getint("alert", "max_subject_len",
                                                default=DEFAULT_MAX_SUBJECT_LEN)

        if self.alert_level < 1:
            self.log.error("Invalid alert level: %d, setting to %d",
                                    self.alert_level, DEFAULT_ALERT_LEVEL)
            self.alert_level = DEFAULT_ALERT_LEVEL

    def admin_emails(self):
        """Return a list of admins that have an email address."""

        session = meta.Session()
        rows = session.query(UserProfile).\
            filter(UserProfile.roleid > 0).\
            filter(UserProfile.email != "").\
            all()

        return [entry.email for entry in rows]

    def publisher_email(self, data):
        """Return a list with the publisher_email for the user
           if it exists and has an email address."""

        if not 'system_users_id' in data:
            return []

        session = meta.Session()
        try:
            entry = session.query(UserProfile).\
                filter(UserProfile.system_users_id == data['system_users_id']).\
                filter(UserProfile.email != "").\
                one()
        except NoResultFound, e:
            return []

        return [entry.email]

    def send(self, event_entry, data):
        """Send an alert.
            Arguments:
                key:    The key to look up.
                data:   A Dictionary with the event information.
        """

        subject = event_entry.subject
        if subject.find("%") == -1:
            # If no substitution is specified in the subject template,
            # use a default one that adds the level:
            subject = "Severity level: %s. %s" % \
                (EventControl.level_strings[event_entry.level],
                                                event_entry.subject)

        else:
            # Use the data dict it for template substitution.
            try:
                subject = subject % data
            except (ValueError, KeyError) as e:
                subject = "Template subject conversion failure: " + str(e) + \
                    "subject: " + subject + \
                    ", data: " + str(data)

        message = event_entry.email_message
        if message:
            try:
                mako_template = Template(message)
                message = mako_template.render(**data)
            except:
                message = "Mako template message conversion failure: " + \
                    exceptions.text_error_template().render() + \
                    "\ntemplate: " + message + \
                        "\ndata: " + str(data)
        else:
           message = self.make_default_message(event_entry, subject, data)

        if not message:
            # message is empty, set it to be the subject
            message = subject

        if not self.enabled:
            self.log.info(\
                "Alerts disabled.  Not sending: Subject: %s, Message: %s",
                                                            subject, message)
            return

        if event_entry.key == EventControl.EXTRACT_OK:
            to_emails = self.publisher_email(data)
        elif event_entry.key == EventControl.EXTRACT_FAILED:
            to_emails = self.admin_emails() + self.publisher_email(data)
        else:
            to_emails = self.admin_emails()

        if not to_emails:
            self.log.debug(\
                "No non-admin users exist with email addresses.  " + \
                "Not sending: Subject: %s, Message: %s", subject, message)
            return

        msg = MIMEText(message)

        if len(subject) > self.max_subject_len:
            subject = subject[:self.max_subject_len]  + "..."

        msg['Subject'] = "Palette Alert: " + subject
        msg['From'] = self.from_email
        msg['To'] = ', '.join(to_emails)
        msg_str = msg.as_string()

        try:
            mail_server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            mail_server.sendmail(self.from_email, to_emails, msg_str)
            mail_server.quit()
        except (smtplib.SMTPException, EnvironmentError) as e:
            self.log.error(\
                "Email send failed, text: %s, exception: %s, server: %s," + \
                " port: %d",
                message, e, self.smtp_server, self.smtp_port)
            return

        self.log.info("Emailed alert: Subject: '%s', message: '%s'" % \
                                                        (subject, message))

        return

    def make_default_message(self, event_entry, subject, data):
        """Given the event entry, subject (string)and data (dictionary),
        return a formatted message, according to the alert level.  The higher
        the alert level, the more details the user will receive.
            alert level 1:
                Only 'stderr'.

            alert level 2:
                stderr, stdout, exit status

            alert level 3:
                Everything including XID, run-status, etc.

            Arguments:
                subject  The subject for the alert message.
                data     The 'data' dictionary which is a response
                         from the agent or well-known key-value pairs (see below)
        """


        message = ""
        if self.alert_level < 1:   # too minimal, not even errors included.
            return subject
        elif self.alert_level >= 3:
            # Include every key we get, even keys we may not know about:
            for key in sorted(data.keys()):
                message += self.indented(key, data[key], always_include=True)
            return message

        # Typical alert levels here: 1 and 2.
        message += "Event: " + subject + "\n"
        message += "Severity level: %s" % \
                        EventControl.level_strings[event_entry.level] + '\n'

        if 'displayname' in data:
            message += "Agent: %s" % data['displayname'] + '\n'
        if 'agent_type' in data:
            message += "Agent type: %s" % data['agent_type'] + '\n'
        if data.has_key('error'):
            message += self.indented("Issue", data['error']) + '\n'

        if data.has_key('info') and data['info']:
            message += self.indented("Additional information",
                                                    data['info']) + '\n'

        # Include stderr, unless it is a duplicate of data['error']
        if data.has_key('stderr'):
            if not data.has_key('error') or (data['stderr'] != data['error']):
                message += self.indented('Error', data['stderr'])

        # Include stdout
        if data.has_key('stdout'):
            message += self.indented("Output", data['stdout'])

        if self.alert_level == 2:
            # Add a bit more for level 2.
            if data.has_key("xid"):
                message += "XID: %d\n" % data['xid']
            if data.has_key("exit-status"):
                message += "Exit status: %d\n" % data['exit-status']

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
