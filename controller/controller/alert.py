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
        self.smtp_port = config.get("alert", "smtp_port", default=25)

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
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.sendmail(self.from_email, [self.to_email], msg_str)
            server.quit()
        except (smtplib.SMTPException, EnvironmentError) as e:
            self.log.error("Email send failed, text: %s, exception: %s",
                text, e)
            return

        self.log.info("Emailed event: " + text)

        return
