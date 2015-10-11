""" Email sender (via postflix) """
# pylint: enable=relative-import,missing-docstring
from __future__ import absolute_import

import logging
import smtplib
from email.mime.text import MIMEText
from email.header import Header

SMTP_HOST = 'localhost'
SMTP_PORT = 25

DEFAULT_MAX_SUBJECT_LEN = 1000

logger = logging.getLogger()

class Mailer(object):
    """ Main email handler. """

    def __init__(self, sender, host=SMTP_HOST, port=SMTP_PORT,
                 max_subject_len=DEFAULT_MAX_SUBJECT_LEN):
        self.sender = sender
        self.smtp_host = host
        self.smtp_port = port
        self.max_subject_len = max_subject_len

    def send_msg(self, recipients, subject, msg, bcc=None):
        """ Send a generic MIME message object"""

        if isinstance(recipients, basestring):
            recipients = [email.strip() for email in recipients.split(',')]
        if bcc and isinstance(bcc, basestring):
            bcc = [email.strip() for email in bcc.split(',')]

        if len(subject) > self.max_subject_len:
            subject = subject[:self.max_subject_len]  + "..."

        subject = Header(unicode(subject), 'utf-8')
        msg['Subject'] = subject
        msg['From'] = self.sender

        if recipients:
            msg['To'] = ', '.join(recipients)
        if bcc:
            for recipient in bcc:
                if recipient not in recipients:
                    recipients.append(recipient)

        try:
            mail_server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            mail_server.sendmail(self.sender, recipients, msg.as_string())
            mail_server.quit()
        except (smtplib.SMTPException, EnvironmentError) as ex:
            logger.error("Email send failed, text: %s, exception: %s, "
                         "server: %s, port: %d",
                         msg.as_string(), ex, self.smtp_host, self.smtp_port)
            return False

        logger.info("Emailed alert: To: '%s' Subject: '%s', message: '%s'",
                    ",".join(recipients), subject, msg.as_string())
        return True

    def send(self, recipients, subject, message, bcc=None):
        """ Send a generic (plain-text) message """

        # Convert from Unicode to utf-8
        message = message.encode('utf-8')    # prevent unicode exception
        try:
            msg = MIMEText(message, "plain", "utf-8")
        except StandardError, ex:
            logger.exception(ex)
            return False

        return self.send_msg(recipients, subject, msg, bcc=bcc)
