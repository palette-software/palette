# This module is named licensing to avoid the Python reserved keyword 'license'.

import urllib
import httplib
import json
import re
import datetime

from sqlalchemy import Column, Integer, BigInteger, DateTime, Boolean, String
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.schema import ForeignKey

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from event_control import EventControl
from manager import Manager
from mixin import BaseMixin, BaseDictMixin

from agent import Agent
from agentmanager import AgentManager
from domain import Domain
from general import SystemConfig
from yml import YmlEntry

class LicenseException(Exception):
    def __init__(self, status, reason):
        message = str(status) + ' ' + reason
        Exception.__init__(self, message)
        self.status = status
        self.reason = reason

class LicenseEntry(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = 'license'

    LICENSE_TYPE_NAMED_USER = "Named-user"
    LICENSE_TYPE_CORE = "Core"

    licenseid = Column(BigInteger, primary_key=True)
    agentid = Column(BigInteger, ForeignKey("agent.agentid"),
                     nullable=False, unique=True)
    interactors = Column(Integer)
    viewers = Column(Integer)
    cores = Column(Integer)
    license_type = Column(String)
    notified = Column(Boolean, nullable=False, default=False)
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
        if cores and cores.isdigit():
            entry.cores = cores

        if entry.cores:
            entry.license_type = LicenseEntry.LICENSE_TYPE_CORE
        elif entry.interactors or entry.viewers:
            entry.license_type = LicenseEntry.LICENSE_TYPE_NAMED_USER

        # If the entry is valid, reset the notification field.
        if entry.valid():
            entry.notified = False

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

        if entry.invalid():
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

            if not entry.notified:
                # Generate an event
                data = agent.todict()
                data['error'] = msg
                server.event_control.gen(EventControl.LICENSE_INVALID, data)
                entry.notified = True
                session.commit()
            return server.error("License invalid on '%s': %s" % \
                                (agent.displayname, msg))

        if entry.notified:
            # License was invalid, but is now valid.
            # There is no event for this, but remember that the license
            # is valid so if it becomes invalid again, the user will get
            # an event.
            entry.notified = False
            session.commit()

        return license_data

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

        server = self.server
        envid = server.environment.envid

        data = {}
        entry = Domain.getone()
        data['license-key'] = entry.license_key
        data['system-id'] = entry.systemid
        data['expiration-time'] = entry.expiration_time
        data['contact-time'] = entry.contact_time
        data['trial'] = entry.trial

        data['palette-version'] = self.server.system.get(
                                        SystemConfig.PALETTE_VERSION,
                                        default='unknown')

        try:
            agent = meta.Session.query(Agent).\
               filter(Agent.agent_type == AgentManager.AGENT_TYPE_PRIMARY).\
               one()

        except NoResultFound:
#            print "No primary agents ever connected."
            return data

        entry = LicenseEntry.get_by_agentid(agent.agentid)
        if not entry:
            self.server.log.debug("No tableau license entry yet.")
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

    def verify(self):
        # pylint: disable=too-many-return-statements
        entry = Domain.getone()
        if not entry.license_key:
            # If there is no license key, don't bother checking the
            # validity of it or attempt to contact the palette
            # license server.
            self.server.log.debug("license verify: No license key.")
            return {'status': "OK", "info": "No license key"}

        data = self.info()
        if not 'license-type' in data:
            self.server.log.debug(
                            "license verify: No tableau license info yet.")
            return {'status': "OK", "info": "No tableau license info yet."}

        try:
            body = self._send(data)
        except IOError as ex:
            self.server.log.debug(
                    "license send exception failed with status %s", ex)
            self._callfailed(str(ex), str(ex))
            return {"error": str(ex)}
        except LicenseException as ex:
            self.server.log.debug(
                    "license send exception failed with status %d, reason %s",
                                                        ex.status, ex.reason)
            self._callfailed(ex.reason, ex.status)
            return {"error": str(ex)}

        # FIXME: Use real reply
        body['trial'] = True
        body['expiration'] = "2015-02-28 00:00:00"

        if not 'trial' in body:
            self.server.log.debug('no trial value in reply: %s', str(body))
            self._callfailed("Invalid reply from license server")
            return {"error": "Invalid reply from license server"}

        if not 'expiration' in body:
            self.server.log.debug("No expiration value in reply: %s", str(body))
            self._callfailed("License reply invalid")
            return {"error": "License reply invalid: " + str(body)}

        entry.trial = body['trial']
        entry.expiration_time = body['expiration']
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
            self.server.log.debug("phone home failed with status %d: %s",
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
                self.server.log.debug("Silence time: %d <= max of: %d",
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

        self.server.log.debug("failure hours was longer than: %d : %d",
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
