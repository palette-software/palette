""" Email limiter """

import logging
from sqlalchemy import Column, BigInteger, DateTime, func
from sqlalchemy.schema import ForeignKey

import akiri.framework.sqlalchemy as meta

from event_control import EventControl
from manager import Manager
from system import SystemKeys

logger = logging.getLogger()

class EmailLimitEntry(meta.Base):
    # pylint: disable=no-init
    __tablename__ = "email_sent"

    emailid = Column(BigInteger, unique=True, nullable=False,
                     autoincrement=True, primary_key=True)

    envid = Column(BigInteger, ForeignKey("environment.envid"))

    eventid = Column(BigInteger)    # Just kept to help. Not required.
    creation_time = Column(DateTime, server_default=func.now())

    @classmethod
    def remove_all(cls, envid):
        session = meta.Session()
        session.query(EmailLimitEntry).\
            filter(EmailLimitEntry.envid == envid).\
            delete()
        session.commit()

class EmailLimitManager(Manager):
    """ Ensures that email is not sent too frequently. """

    def _log_email(self, eventid):
        session = meta.Session()
        entry = EmailLimitEntry(envid=self.envid, eventid=eventid)
        session.add(entry)
        session.commit()

    def _prune(self):
        """Keep only the the ones in the last email-lookback-minutes
           period."""

        email_lookback_minutes = self.system[SystemKeys.EMAIL_LOOKBACK_MINUTES]
        stmt = ("DELETE from email_sent "
                "where creation_time < NOW() - INTERVAL '%d MINUTES'") % \
                (email_lookback_minutes,)

        connection = meta.get_connection()
        result = connection.execute(stmt)
        connection.close()

        logger.debug("email limit manager: pruned %d", result.rowcount)

    def _recent_count(self):
        return meta.Session.query(EmailLimitEntry).\
            filter(EmailLimitEntry.envid == self.envid).\
            count()

    def email_limit_reached(self, event_entry, eventid):
        """Keep track of how many emails have been sent during the last
           email-lookback-minutes period and check to see if
           email-max-count have already been sent.  Return:
                count-of-emails-sent-recently:  if email_limit reached
                                                reached (don't send more
                                                emails).
                False if email-limit hasn't been reached (keep sending emails).
        """

        logger.debug("email_limit_reached checking: event %s, eventid %d\n",
                       event_entry.key, eventid)

        # We limit only ERROR events.
        if event_entry.level != 'E' or \
            event_entry.key in [EventControl.EMAIL_TEST,
                                                    EventControl.EMAIL_SPIKE]:
            # These events can always be emailed and don't count against
            # the maximum.
            return False

        self._log_email(eventid)
        self._prune()   # Keep only the last email-looback-minutes rows

        emails_sent_recently = self._recent_count()
        email_lookback_minutes = self.system[SystemKeys.EMAIL_LOOKBACK_MINUTES]
        logger.debug("email_limit: sent %d error emails in the last "
                       "%d minutes.",
                       emails_sent_recently, email_lookback_minutes)

        email_max_count = self.system[SystemKeys.EMAIL_MAX_COUNT]
        if emails_sent_recently > email_max_count:
            # Don't sent this email alert
            # send an alert that we're disabling email alerts
            self._eventit()
            # Disable email alerts
            self.system[SystemKeys.ALERTS_ADMIN_ENABLED] = False
            self.system[SystemKeys.ALERTS_PUBLISHER_ENABLED] = False
            self.system[SystemKeys.EMAIL_SPIKE_DISABLED_ALERTS] = True
            meta.commit()
            return emails_sent_recently

        # Send this email alert
        return False

    def _eventit(self):
        """Send the EMAIL-SPIKE event."""

        email_lookback_minutes = self.system[SystemKeys.EMAIL_LOOKBACK_MINUTES]
        email_max_count = self.system[SystemKeys.EMAIL_MAX_COUNT]
        data = {'email_lookback_minutes': email_lookback_minutes,
                'email_max_count': email_max_count}

        self.server.event_control.gen(EventControl.EMAIL_SPIKE, data)
