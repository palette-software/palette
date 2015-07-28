#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import traceback
import smtplib
import datetime
from email.mime.text import MIMEText
from email.header import Header
from sqlalchemy.orm.exc import NoResultFound

import akiri.framework.sqlalchemy as meta

from domain import Domain
from general import SystemConfig
from event_control import EventControl
from email_limit import EmailLimitManager
from profile import UserProfile
from licensing import LicenseManager
from util import UNDEFINED

from mako.template import Template
from mako import exceptions
import mako.runtime
mako.runtime.UNDEFINED = UNDEFINED

class AlertEmail(object):
    #pylint: disable=too-many-instance-attributes

    DEFAULT_ALERTS_ENABLED = False
    DEFAULT_ALERT_LEVEL = 1
    DEFAULT_MAX_SUBJECT_LEN = 1000

    def __init__(self, server, standalone=False):
        if standalone:
            self.envid = 1
            self.standalone = True
            self.to_email = "tim.flagg@gmail.com"
            self.smtp_server = "localhost"
            self.smtp_port = 25
            self.alert_level = 1
            self.enabled = 1
            self.max_subject_len = 100
            import logging

            logging.basicConfig(level=logging.DEBUG)
            self.log = logging
            return
        self.envid = server.environment.envid
        self.standalone = False
        self.config = server.config
        self.system = server.system
        self.st_config = SystemConfig(server.system)
        self.log = server.log
        self.server = server
        self.admin_enabled = True
        self.email_limit_manager = EmailLimitManager(server)

        # Check to see if alert enabled/disabled is configured in the
        # system table.  If not, 1) Use the *ini file or if not there,
        # 2) default value and set that value in the system table.
        try:
            self.enabled = self.st_config.alerts_enabled
        except ValueError:
            # Alerts aren't in the system table, so check the *ini file.
            self.enabled = self.config.getboolean('alert', 'enabled',
                                       default=self.DEFAULT_ALERTS_ENABLED)

            # Set this value in the system table.
            if self.enabled:
                value = 'yes'
            else:
                value = 'no'
            self.system.save(SystemConfig.ALERTS_ENABLED, value)


        self.smtp_server = self.config.get('alert', 'smtp_server',
                                    default="localhost")
        self.smtp_port = self.config.getint("alert", "smtp_port", default=25)

        self.alert_level = self.config.getint("alert", "alert_level",
                                        default=self.DEFAULT_ALERT_LEVEL)

        self.max_subject_len = self.config.getint("alert", "max_subject_len",
                                        default=self.DEFAULT_MAX_SUBJECT_LEN)

        if self.alert_level < 1:
            self.log.error("Invalid alert level: %d, setting to %d",
                           self.alert_level, self.DEFAULT_ALERT_LEVEL)
            self.alert_level = self.DEFAULT_ALERT_LEVEL

    def admin_emails(self):
        """Return a list of admins that have an email address, enabled
           and aren't the palette user."""

        if self.standalone:
            return [self.to_email]

        if not self.admin_enabled:
            return []

        session = meta.Session()
        rows = session.query(UserProfile).\
            filter(UserProfile.roleid > 0).\
            filter(UserProfile.email != None).\
            filter(UserProfile.email_level > 0).\
            filter(UserProfile.userid != 0).\
            all()

        return [entry.email for entry in rows]

    def publisher_email(self, data):
        """Return a list with the publisher_email for the user
           if it exists and has an email address."""

        if not 'system_user_id' in data:
            return []

        try:
            publisher_enabled = self.st_config.alerts_publisher_enabled
        except ValueError:
            # If not there, then set to enabled
            publisher_enabled = True
        if not publisher_enabled:
            return []

        session = meta.Session()
        try:
            entry = session.query(UserProfile).\
                filter(UserProfile.system_user_id == data['system_user_id']).\
                filter(UserProfile.email != None).\
                filter(UserProfile.email_level > 0).\
                one()
        except NoResultFound:
            return []

        return [entry.email]

    def send(self, event_entry, data, recipient=None, eventid=None):
        """Send an alert.
            Arguments:
                key:    The key to look up.
                data:   A Dictionary with the event information.
        """
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-return-statements

        try:
            self.admin_enabled = self.st_config.alerts_admin_enabled
        except ValueError:
            # If not there, then set to enabled
            self.admin_enabled = True

        subject = event_entry.email_subject
        if subject == None:
            subject = event_entry.subject

        if subject.find("%") != -1:
            # Use the data dict for template substitution.
            try:
                subject = subject % data
            except (ValueError, KeyError) as ex:
                subject = "Template subject conversion failure: " + str(ex) + \
                    "subject: " + subject + \
                    ", data: " + str(data)

        message = event_entry.email_message
        if message:
            try:
                mako_template = Template(message)
                message = mako_template.render(**data)
            except StandardError:
                message = "Mako template message conversion failure: " + \
                    exceptions.text_error_template().render() + \
                    "\ntemplate: " + message + \
                        "\ndata: " + str(data)
        else:
            message = self.make_default_message(event_entry, subject, data)

        if not message:
            # message is empty, set it to be the subject
            message = subject

        if recipient:
            # Force to only one test recipient.
            # It is sent even if alerts are disabled.
            to_emails = [recipient]
        else:
            try:
                self.enabled = self.st_config.alerts_enabled
            except ValueError:
                self.enabled = self.DEFAULT_ALERTS_ENABLED

            if not self.enabled:
                self.log.info(
                    "Alerts disabled.  Not sending: Subject: %s, Message: %s",
                    subject, message)
                return

            if event_entry.key in (EventControl.EXTRACT_OK,
                                   EventControl.EXTRACT_FAILED):
                to_emails = self.admin_emails() + self.publisher_email(data)
            else:
                to_emails = self.admin_emails()

        # Remove any duplicates
        to_emails = list(set(to_emails))

        bcc = None
        if not self.standalone and self.admin_enabled and not recipient:
            # Get the diagnostics email and bcc it there if it exists.
            entry = UserProfile.get(self.envid, 0)
            if entry and entry.email != None and entry.email != "":
                bcc = [entry.email]

        if not to_emails and not bcc:
            self.log.debug(
                "No admin users exist with enabled email addresses.  " + \
                "Not sending: Subject: %s, Message: %s", subject, message)
            return

        # Send only PHONE-HOME related events if their palette license
        # has expired.
        if event_entry.key not in [EventControl.PHONE_HOME_FAILED,
                                   EventControl.PHONE_HOME_OK,
                                   EventControl.EMAIL_TEST]:
            entry = Domain.getone()
            if entry.expiration_time and \
                            datetime.datetime.utcnow() > entry.expiration_time:
                self.log.debug("License expired. " +
                                    "Not sending: Subject: %s, Message: %s",
                                    subject, message)
                return

            if entry.contact_time:
                silence_time = (datetime.datetime.utcnow() - \
                                        entry.contact_time).total_seconds()
                if silence_time > LicenseManager.MAX_SILENCE_TIME:
                    self.log.debug("Phonehome contact time is %d > %d. " +
                                    "Not sending: Subject: %s, Message: %s",
                                    silence_time,
                                    LicenseManager.MAX_SILENCE_TIME,
                                    subject, message)
                    return

        if self.email_limit_manager.email_limit_reached(event_entry, eventid):
            return

        # Convert from Unicode to utf-8
        message = message.encode('utf-8')    # prevent unicode exception
        try:
            msg = MIMEText(message, "plain", "utf-8")
        except StandardError:
            # pylint: disable=unused-variable
            exc_type, exc_value, exc_traceback = sys.exc_info()
            tbstr = ''.join(traceback.format_tb(exc_traceback))
            report = "Error: %s.  Traceback: %s." % (sys.exc_info()[1], tbstr)
            self.log.error("alert send: MIMEText() failed for message." + \
                           "will not send message: '%s'. %s" % \
                           (message, report))

            return

        if len(subject) > self.max_subject_len:
            subject = subject[:self.max_subject_len]  + "..."

        subject = Header(unicode(subject), 'utf-8')
        msg['Subject'] = subject
        from_email = self.st_config.from_email
        msg['From'] = from_email

        all_to = []

        if to_emails:
            msg['To'] = ', '.join(to_emails)
            all_to += to_emails
        if bcc:
            all_to += bcc

        msg_str = msg.as_string()

        try:
            mail_server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            mail_server.sendmail(from_email, all_to, msg_str)
            mail_server.quit()
        except (smtplib.SMTPException, EnvironmentError) as ex:
            self.log.error(
                "Email send failed, text: %s, exception: %s, server: %s," + \
                " port: %d",
                message, ex, self.smtp_server, self.smtp_port)
            return

        self.log.info("Emailed alert: Subject: '%s', message: '%s'",
                                                    subject, message)

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
                         from the agent or well-known key-value pairs
                         (see below)
        """
        # pylint: disable=too-many-branches

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
