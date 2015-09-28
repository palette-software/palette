#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import traceback
import smtplib
from datetime import datetime
import threading
from email.mime.text import MIMEText
from email.header import Header
from sqlalchemy.orm.exc import NoResultFound

import akiri.framework.sqlalchemy as meta

from agent import Agent
from domain import Domain
from event_control import EventControl
from email_limit import EmailLimitManager
from profile import UserProfile
from system import SystemKeys
from util import UNDEFINED

from mako.template import Template
from mako import exceptions
import mako.runtime
mako.runtime.UNDEFINED = UNDEFINED

class AlertEmail(object):
    #pylint: disable=too-many-instance-attributes

    DEFAULT_ALERT_LEVEL = 1
    DEFAULT_MAX_SUBJECT_LEN = 1000

    def __init__(self, server):
        self.envid = server.environment.envid
        self.config = server.config
        self.system = server.system
        self.log = server.log
        self.server = server
        self.email_limit_manager = EmailLimitManager(server)

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

    def admin_emails(self, event_entry):
        """Return a list of admins that have an email address, enabled
           and aren't the palette user."""

        if not self.system[SystemKeys.ALERTS_ADMIN_ENABLED] and \
                event_entry.key != EventControl.EMAIL_DISABLED_REMINDER:
            # If admin emails are disabled and it isn't the
            # EMAIL_DISABLED_REMINDER, then don't send email to any admins.
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

        if not 'userid' in data:
            return []

        if not self.system[SystemKeys.ALERTS_PUBLISHER_ENABLED]:
            return []

        session = meta.Session()
        try:
            entry = session.query(UserProfile).\
                filter(UserProfile.userid == data['userid']).\
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

        subject = event_entry.email_subject
        if subject == None:
            subject = event_entry.subject

        if subject.find("%") != -1:
            # Use the data dict for template substitution.
            try:
                subject = subject % data
            except (ValueError, KeyError) as ex:
                subject = "Email Template subject conversion failure: " + \
                    str(ex) + \
                    "subject: " + subject + \
                    ", data: " + str(data)

        message = event_entry.email_message
        if message:
            try:
                mako_template = Template(message)
                message = mako_template.render(**data)
            except StandardError:
                message = "Email mako template message conversion failure: " + \
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
            if not self.system[SystemKeys.ALERTS_ENABLED]:
                self.log.info(
                    "Alerts disabled.  Not sending: Subject: %s, Message: %s",
                    subject, message)
                return

            to_emails = []

            if event_entry.publisher_visibility:
                to_emails = self.publisher_email(data)
            if event_entry.admin_visibility:
                to_emails += self.admin_emails(event_entry)

        # Remove any duplicates
        to_emails = list(set(to_emails))

        bcc = None
        if self.system[SystemKeys.ALERTS_ADMIN_ENABLED] and not recipient:
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
                            datetime.utcnow() > entry.expiration_time:
                self.log.debug("License expired. " +
                                    "Not sending: Subject: %s, Message: %s",
                                    subject, message)
                return

            if entry.contact_time:
                silence_time = (datetime.utcnow() - \
                                        entry.contact_time).total_seconds()
                max_silence_time = self.system[SystemKeys.MAX_SILENCE_TIME]
                if silence_time > max_silence_time and max_silence_time != -1:
                    self.log.debug("Phonehome contact time is %d > %d. " +
                                    "Not sending: Subject: %s, Message: %s",
                                    silence_time, max_silence_time,
                                    subject, message)
                    return

        if self.email_limit_manager.email_limit_reached(event_entry, eventid):
            return

        sendit = True
#        print '\n------------event key is', event_entry.key
        if self.system[SystemKeys.EMAIL_MUTE_RECONNECT_SECONDS]:
            # Potentially mute the connect or reconnect emails.
            if event_entry.key == EventControl.AGENT_DISCONNECT:
                self._mute_dis_check(data, to_emails, bcc, subject, message)
                # If the event is emailed, it is done there,
                # after a delay
                return

            elif event_entry.key in [EventControl.AGENT_COMMUNICATION,
                                     EventControl.INIT_STATE_STARTED,
                                     EventControl.INIT_STATE_STOPPED,
                                     EventControl.INIT_STATE_DEGRADED]:
                sendit = self._mute_reconn_check(data)

        if sendit:
            self._do_send(to_emails, bcc, subject, message)

    def _mute_reconn_check(self, data):
        """
            Send a reconnect event email only if the reconnect happened
            after EMAIL_MUTE_RECONNECT_SECONDS.
        """
        if not 'agentid' in data:
            self.log.error("_mute_reconn_check: missing 'agentid': %s",
                            str(data))
            return True

        agentid = data['agentid']
        entry = Agent.get_by_id(agentid)
        if not entry:
            self.log.error("_mute_reconn_check: No old row for agentid %d",
                           agentid)
            return True

        if not entry.last_disconnect_time:
            return True

        timedelta = int((datetime.utcnow() - \
                        entry.last_disconnect_time).total_seconds())
        if timedelta <= self.system[SystemKeys.EMAIL_MUTE_RECONNECT_SECONDS]:
            self.log.debug("_mute_reconn_check: Will not send reconnect "
                           "email, too soon, timedelta: %d", timedelta)
#            print "will not send reconnect: too soon", timedelta
            return False    # Don't send the reconnect email
#        print "will send reconnect email", timedelta
        self.log.debug("_mute_reconn_check: Will send reconnect "
                       "email, timedelta: %d", timedelta)
        return True         # send the reconenct email

    def _mute_dis_check(self, data, to_emails, bcc, subject, message):
        """For poor network connections between an agent and the controller,
           don't send email or disconnect or reconnect events that occur
           in less than EMAIL_MUTE_RECONNECT_SECONDS, if set.
        """
        # pylint: disable=too-many-arguments

        if not self.system[SystemKeys.EMAIL_MUTE_RECONNECT_SECONDS]:
            return True

        tobj = threading.Thread(target=self._dis_thread,
                args=(data, to_emails, bcc, subject, message))
        tobj.daemon = True
        tobj.start()

    def _dis_thread(self, data, to_emails, bcc, subject, message):
        """
            Send a disconnect event email only if:
                  The agent is still disconnected after the agent is
                  still disconnected after
                      EMAIL_MUTE_RECONNECT_SECONDS
        """
        # pylint: disable=too-many-arguments

#        print "dis thread for", subject
        self.log.debug("_dis_thread for subject %s", subject)
        if not 'agentid' in data:
            self.log.error("_dis_thread: missing 'agentid': %s", str(data))
            return
        agentid = data['agentid']

        old_entry = Agent.get_by_id(agentid)
        if not old_entry:
            self.log.error("_dis_thread: No old row for agentid %d",
                       agentid)
            return
        old_last_disconnect_time = old_entry.last_disconnect_time

#        print "about to sleep"
        time.sleep(float(self.system[SystemKeys.EMAIL_MUTE_RECONNECT_SECONDS]))
#        print "woke up"
        meta.Session.expire(old_entry)
        entry = Agent.get_by_id(agentid)
        if not entry:
            self.log.error("_dis_thread: No row for agentid %d", agentid)
            return
#        print "dis:\nold last_disconnect_time", old_last_disconnect_time
#        print "new last_disconnect_time", entry.last_disconnect_time
#        print "last_connection_time", entry.last_connection_time
        if entry.connected():
#            print 'now connected'
            self.log.debug("_dis_thread: agentid %d now connected.", agentid)
            return

#        print "not connected"

        if old_last_disconnect_time != entry.last_disconnect_time:
#            print "disconnect time changed"
            self.log.debug("_dis_thread: agentid %d disconnect time changed. "
                           "Ignoring.", agentid)
            return

        self.log.debug("_dis_thread: sending email for agentid %d: %s",
                       agentid, subject)
        self._do_send(to_emails, bcc, subject, message)

    def _do_send(self, to_emails, bcc, subject, message):
        # pylint: disable=too-many-locals

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
        from_email = self.system[SystemKeys.FROM_EMAIL]
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

#        print 'email sent', subject

        self.log.info("Emailed alert: To: '%s' Subject: '%s', message: '%s'",
                                                str(all_to), subject, message)

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
