# This module is named licensing to avoid the Python reserved keyword 'license'.

import logging
import urllib
import httplib
import json
import re
import datetime

from sqlalchemy import Column, Integer, BigInteger, DateTime, Boolean, String
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.schema import ForeignKey

import akiri.framework.sqlalchemy as meta

from event_control import EventControl
from manager import Manager
from mixin import BaseMixin, BaseDictMixin
from util import version

from agent import Agent
from agentmanager import AgentManager
from domain import Domain
# from general import SystemConfig
from yml import YmlEntry


LICENSING_URL = "https://licensing.palette-software.com"

def licensing_send(uri, data):
    params = urllib.urlencode(data)

    conn = urllib.urlopen(LICENSING_URL + uri, params)
    reply_json = conn.read()
    conn.close()

    if conn.getcode() != httplib.OK:
        logging.warn("phone home failed with status %d: %s",
                     conn.getcode(), reply_json)
        raise LicenseException(conn.getcode(),
                               "Failed with status %d. Reply: %s " % \
                               (conn.getcode(), reply_json))

    return json.loads(reply_json)

def licensing_info(domain, envid):
    """Don't do anything very active since this can run when
    in UPGRADE state, etc."""

    data = {}
    data['license-key'] = domain.license_key
    data['system-id'] = domain.systemid
    data['expiration-time'] = domain.expiration_time
    data['contact-time'] = domain.contact_time
    data['trial'] = domain.trial

    # FIXME: use the version() function when sorted out.
    data['palette-version'] = version()

    try:
        agent = meta.Session.query(Agent).\
                filter(Agent.agent_type == AgentManager.AGENT_TYPE_PRIMARY).\
                one()
    except NoResultFound:
        #            print "No primary agents ever connected."
        return data

    entry = LicenseEntry.get_by_agentid(agent.agentid)
    if not entry:
        logging.debug("No tableau license entry yet.")
        return data

    data['license-type'] = entry.license_type

    if entry.license_type == LicenseEntry.LICENSE_TYPE_NAMED_USER:
        data['license-quantity'] = entry.interactors
    elif entry.license_type == LicenseEntry.LICENSE_TYPE_CORE:
        data['license-quantity'] = entry.cores
    else:
        data['license-quantity'] = None

    data['tableau-version'] = YmlEntry.get(envid, 'version.external',
                                           default='unknown')

    data['tableau-bitness'] = YmlEntry.get(envid, 'version.bitness',
                                           default='unknown')

    data['processor-type'] = agent.processor_type
    data['processor-count'] = agent.processor_count
    data['processor-bitness'] = agent.bitness
    data['primary-uuid'] = agent.uuid

    return data


class LicenseException(StandardError):
    def __init__(self, status, reason):
        message = str(status) + ' ' + reason
        StandardError.__init__(self, message)
        self.status = status
        self.reason = reason

class LicenseEntry(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = 'license'

    LICENSE_TYPE_NAMED_USER = "Named-user"
    LICENSE_TYPE_CORE = "Core"

    licenseid = Column(BigInteger, primary_key=True)
    agentid = Column(BigInteger,
                    ForeignKey("agent.agentid", ondelete='CASCADE'),
                     nullable=False, unique=True)
    interactors = Column(Integer)
    viewers = Column(Integer)
    cores = Column(Integer)
    license_type = Column(String)
    notified = Column(Boolean, nullable=False, default=False) # deprecated
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(),
                               onupdate=func.current_timestamp())

    @classmethod
    def get_by_agentid(cls, agentid):
        try:
            entry = meta.Session.query(LicenseEntry).\
                filter(LicenseEntry.agentid == agentid).\
                one()
        except NoResultFound:
            return None
        return entry

    @classmethod
    def get(cls, agentid, interactors=None, viewers=None, cores=None):
        session = meta.Session()
        entry = cls.get_by_agentid(agentid)
        if not entry:
            entry = LicenseEntry(agentid=agentid)
            session.add(entry)

        if interactors and interactors.isdigit():
            entry.interactors = int(interactors)
        if viewers and viewers.isdigit():
            entry.viewers = int(viewers)
        if cores:
            entry.cores = cores

        if entry.cores:
            entry.license_type = LicenseEntry.LICENSE_TYPE_CORE
        else:
            # Default setting to let us know the license info have been
            # received. It could be 0 interactors and 0 viewers, which
            # means "no license".
            entry.license_type = LicenseEntry.LICENSE_TYPE_NAMED_USER

        return entry

    @classmethod
    def all(cls):
        return cls.get_all_by_keys({})

    @classmethod
    def parse(cls, output):
        # pylint: disable=anomalous-backslash-in-string
        if output.find("Cores licensed") != -1:
            try:
                cores = int(output.split()[-1])
            except (IndexError, ValueError):
                print "Invalid format for license report:", output
                return {}
            return {'cores': cores}
        pattern = '(?P<interactors>\d+) interactors, (?P<viewers>\d+) viewers'
        match = re.search(pattern, output)
        if not match:
            return {}
        return match.groupdict()

    def gettype(self):
        return str(self.license_type)

    def valid(self):
        # pylint: disable=too-many-return-statements
        if self.license_type == LicenseEntry.LICENSE_TYPE_CORE:
            if self.cores:
                return True
            else:
                return False
        elif self.license_type == LicenseEntry.LICENSE_TYPE_NAMED_USER:
            if self.interactors or self.viewers:
                return True
            else:
                return False
        elif self.license_type is None:
            # License hasn't been retrieved yet: OK unless proved otherwise.
            return True

        if self.interactors is None and self.viewers is None and \
                                                        self.cores is None:
            # License hasn't been retrieved yet: OK unless proved otherwise.
            return True

        return False

    def invalid(self):
        return not self.valid()

    def capacity(self):
        if self.interactors is None and self.viewers is None:
            return None
        return "%d interactors, %d viewers" % (self.interactors, self.viewers)


class LicenseManager(Manager):
    MAX_SILENCE_TIME = 72 * 60 * 60     # 72 hours

    def check(self, agent):
        server = self.server

        body = server.cli_cmd('tabadmin license', agent, timeout=60*10)

        if not 'exit-status' in body or body['exit-status'] != 0:
            return body
        if not 'stdout' in body:
            return body

        session = meta.Session()
        output = body['stdout']
        license_data = LicenseEntry.parse(output)
        entry = LicenseEntry.get(agentid=agent.agentid, **license_data)
        session.commit()

        msg = "License type: %s, " % str(entry.license_type)
        if entry.license_type == LicenseEntry.LICENSE_TYPE_NAMED_USER:
            msg += "interactors: %s, viewers: %s" % \
                        (str(entry.interactors), str(entry.viewers))
        elif entry.license_type == LicenseEntry.LICENSE_TYPE_CORE:
            msg += "cores: %s" % str(entry.cores)
        else:
            msg += "interactors: %s, viewers: %s, cores: %s" \
                        % (str(entry.interactors), str(entry.viewers),
                           str(entry.cores))

        notification = self.server.notifications.get("tlicense")

        if entry.valid():
            if notification.color == 'red':
                data = agent.todict()
                data['stdout'] = msg
                self.server.event_control.gen(EventControl.LICENSE_VALID, data)
                # Remember when we sent the notification
                notification.modification_time = func.now()
                notification.color = 'green'
                notification.notified_color = 'green'
                notification.description = None
                session.commit()
            return license_data
        else:
            # license is invalid
            if notification.color != 'red':
                # Generate an event
                data = agent.todict()
                data['error'] = msg
                if notification.color != 'red':
                    self.server.event_control.gen(EventControl.LICENSE_INVALID,
                                                  data)

                notification.color = 'red'
                notification.notified_color = 'red'
                # Remember when we sent the notification
                notification.modification_time = func.now()

                session.commit()
            return server.error("License invalid on '%s': %s" % \
                                (agent.displayname, msg))

    def repair(self, agent):
        server = self.server
        data = agent.todict()

        server.event_control.gen(EventControl.LICENSE_REPAIR_STARTED, data)

        body = server.cli_cmd('tabadmin license --repair_service', agent,
                              timeout=60*10)

        if not 'exit-status' in body or body['exit-status'] != 0:
            data['status'] = 'FAILED'
            if 'stderr' in body:
                data['error'] = body['stderr']
            else:
                data['error'] = 'License repair failed'
            server.event_control.gen(EventControl.LICENSE_REPAIR_FAILED, data)
            server.error("License repair failed on '%s'" % agent.displayname)
        else:
            data['status'] = 'OK'
            server.event_control.gen(EventControl.LICENSE_REPAIR_FINISHED, data)
        return body

    def info(self):
        """Don't do anything very active since this can run when
           in UPGRADE state, etc."""
        entry = Domain.get_by_name(self.server.domainname)
        return licensing_info(entry, self.server.environment.envid)

    def verify(self):
        # pylint: disable=too-many-return-statements
        entry = Domain.getone()
        logging.debug('license verify, license_id: %s', entry.license_key)
        if not entry.license_key:
            # If there is no license key, don't bother checking the
            # validity of it or attempt to contact the palette
            # license server.
            logging.debug("license verify: No license key.")
            return {'status': "OK", "info": "No license key"}

        data = self.info()
        if not 'license-type' in data:
            logging.debug("license verify: No tableau license info yet.")
            return {'status': "OK", "info": "No tableau license info yet."}

        try:
            body = licensing_send('/license', data)
        except IOError as ex:
            logging.debug("license send exception failed with status %s", ex)
            self._callfailed(str(ex), str(ex))
            return {"error": str(ex)}
        except LicenseException as ex:
            logging.debug(
                "license send exception failed with status %d, reason %s",
                ex.status, ex.reason)
            self._callfailed(ex.reason, ex.status)
            return {"error": str(ex)}

        if not 'trial' in body:
            logging.debug('no trial value in reply: %s', str(body))
            self._callfailed("Invalid reply from license server")
            return {"error": "Invalid reply from license server"}

        if not 'expiration-time' in body:
            logging.debug("No expiration value in reply: %s", str(body))
            self._callfailed("License reply invalid")
            return {"error": "License reply invalid: " + str(body)}

        if 'id' in body:
            entry.domainid = int(body['id'])

        entry.trial = body['trial']
        entry.expiration_time = body['expiration-time']
        meta.Session.commit()

        self._callok()

        return body

    def _send(self, data):
        params = urllib.urlencode(data)

        conn = urllib.urlopen(
                        "https://licensing.palette-software.com/license",
                        params)

        reply_json = conn.read()
        conn.close()

        if conn.getcode() != httplib.OK:
            logging.debug("phone home failed with status %d: %s",
                                        conn.getcode(), reply_json)
            raise LicenseException(conn.getcode(),
                "Failed with status %d. Reply: %s " % \
                                            (conn.getcode(), reply_json))

        reply = json.loads(reply_json)

        return reply

    def _callfailed(self, reason, status=None):
        """If answered=True, it answered, but returned an invalid response."""
        session = meta.Session()

        data = {}

        # FIXME: pass as a parameter
        entry = Domain.getone()
        if not entry.contact_failures:
            entry.contact_failures = 1
        else:
            entry.contact_failures += 1

        if status == 404:
            # The license was not found.
            # Set the expiration to now.
            entry.expiration_time = func.now()
            session.commit()
            return

        if entry.contact_time:
#            print "contact_time:", entry.contact_time
#            print "timestamp thing:", datetime.datetime.now()
            silence_time = (datetime.datetime.now() - \
                            entry.contact_time).total_seconds()
            if silence_time <= self.MAX_SILENCE_TIME:
                logging.debug("Silence time: %d <= max of: %d",
                              silence_time, self.MAX_SILENCE_TIME)
                # If they had no expiration time (like on initial install)
                # then expire it now.
                if not entry.expiration_time:
                    entry.expiration_time = func.now()
                session.commit()
                return
            data['failure_hours'] = int((datetime.datetime.now() - \
                                    entry.contact_time).total_seconds() / 3600)
        else:
            # Never connected successfully to the license server.
            # Could happen on initial installation.
            # Give them 72 hours to get this sorted out by pretending
            # they contacted the server on initial attempt.
            entry.contact_time = func.now()
            session.commit()
            return

        session.commit()

        logging.debug("failure hours was longer than: %d : %d",
                      self.MAX_SILENCE_TIME, data['failure_hours'])

        notification = self.server.notifications.get("phonehome")
        notification.description = reason
        if not status is None:
            notification.description += ', status: ' + str(status)

        data['contact_failures'] = entry.contact_failures
        data['last_contact_time'] = entry.contact_time
        data['max_silence_time'] = self.MAX_SILENCE_TIME/(60*60)

        if notification.color != 'red':
            self.server.event_control.gen(EventControl.PHONE_HOME_FAILED, data)

            notification.color = 'red'
            notification.notified_color = 'red'
            # Remember when we sent the notification
            notification.modification_time = func.now()

        session.commit()

    def _callok(self):

        session = meta.Session()
        entry = Domain.getone()
        data = {'contact_failures': entry.contact_failures}

        entry.contact_failures = 0
        entry.contact_time = func.now()

        notification = self.server.notifications.get("phonehome")

        if notification.color == 'red':
            self.server.event_control.gen(EventControl.PHONE_HOME_OK, data)
            notification.modification_time = func.now()
            notification.color = 'green'
            notification.notified_color = 'green'
            notification.description = None

        session.commit()
