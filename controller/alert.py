import smtplib
from email.mime.text import MIMEText

from inits import *

class Alert(object):

    def __init__(self, config, log):
        self.config = config
        self.log = log
        self.enabled = config.getbooleandef('alert', 'enabled', False)
        self.to_email = config.get('alert', 'to_email', "nobody@nowhere.nohow")
        self.from_email = config.get('alert', 'from_email', "alerts@palette-software.com")

    def send(self, text):

        if not self.enabled:
            self.log.info("Alerts disabled.  Not sending: " + text)
            return

        msg = MIMEText(text)

        msg['Subject'] = "Palette Alert: " + text
        msg['From'] = self.from_email
        msg['To'] = self.to_email
        msg_str = msg.as_string()

        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.sendmail(self.from_email, [self.to_email], msg_str)
            server.quit()
        except (smtplib.SMTPException, EnvironmentError) as e:
            self.log.error("Email send failed, text: %s, exception: %s",
                text, e)
            return

        self.log.info("Emailed event: " + text)

        return
