import smtplib
from email.mime.text import MIMEText

from inits import *

class Alert(object):

    def __init__(self, log):
        self.log = log

    def send(self, text):

        if not alerts_enabled:
            self.log.info("Alerts disabled.  Not sending: " + text)
            return

        msg = MIMEText(text)

        msg['Subject'] = "Palette Alert: " + text
        msg['From'] = alert_from_email
        msg['To'] = alert_to_email
        msg_str = msg.as_string()

        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.sendmail(alert_from_email, [alert_to_email], msg_str)
            server.quit()
        except (smtplib.SMTPException, EnvironmentError) as e:
            self.log.error("Email send failed, text: %s, exception: %s",
                text, e)
            return

        self.log.info("Emailed event: " + text)

        return
