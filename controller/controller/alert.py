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
            self.log.error("Email send failed, text: %s, exception: %s, server: %s, port: %d",
                text, e, self.smtp_server, self.smtp_port)
            return

        self.log.info("Emailed event: " + text)

        return

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
