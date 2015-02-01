# This module is named licensing to avoid the Python reserved keyword 'license'.

import urllib
import httplib
import json
import re
import datetime

from sqlalchemy import Column, Integer, BigInteger, DateTime, Boolean
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
    def __init__(self, errmsg):
        Exception.__init__(self, errmsg)

class LicenseEntry(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = 'license'

    licenseid = Column(BigInteger, primary_key=True)
    agentid = Column(BigInteger, ForeignKey("agent.agentid"),
                     nullable=False, unique=True)
    interactors = Column(Integer)
    viewers = Column(Integer)
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
    def get(cls, agentid, interactors=None, viewers=None):
        session = meta.Session()
        entry = cls.get_by_agentid(agentid)
        if not entry:
            entry = LicenseEntry(agentid=agentid)
            session.add(entry)

        entry.interactors = interactors
        entry.viewers = viewers

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
        pattern = '(?P<interactors>\d+) interactors, (?P<viewers>\d+) viewers'
        match = re.search(pattern, output)
        if not match:
            return {}
        return match.groupdict()

    def invalid(self):
        if self.interactors is None:
            return False
        self.interactors = int(self.interactors)
        if self.viewers is None:
            return False
        self.viewers = int(self.viewers)
        return self.interactors == 0 and self.viewers == 0

    def valid(self):
        return not self.invalid()

    def gettype(self):
        if self.interactors is None and self.viewers is None:
            return "Core"
        else:
            return "Named-user"

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
            if not entry.notified:
                # Generate an event
                data = agent.todict()
                data['error'] = "interactors: %s, viewers: %s" % \
                                (entry.interactors, entry.viewers)
                server.event_control.gen(EventControl.LICENSE_INVALID, data)
                entry.notified = True
                session.commit()
            return server.error(\
                "License invalid on '%s': interactors: %s, viewers: %s" % \
                    (agent.displayname, entry.interactors, entry.viewers))

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

    def _info(self):
        """Don't do anything very active since this can run when
           in UPGRADE state, etc."""

        server = self.server
        envid = server.environment.envid

        data = {}
        entry = Domain.getone()
        data['license-key'] = entry.license_key
        # fixme
        data['license-type'] = "Named-user"
        data['license-quantity'] = 10
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
            print "No primary agents ever connected."
            return data

        entry = LicenseEntry.get_by_agentid(agent.agentid)
        if not entry:
            self.server.log.debug("No tableau license entry yet.")
            return data

        data['license-type'] = entry.gettype()
        # fixme
        data['license-type'] = "Named-user"
        data['license-quantity'] = entry.interactors

        data['tableau-quantity'] = entry.viewers

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
        entry = Domain.getone()
        if not entry.license_key:
            # If there is no license key, don't bother checking the
            # validity of it or attempt to contact the palette
            # license server.
            self.log.debug("license verify: No license key.")
            return {'status': "OK", "info": "No license key"}

        data = self._info()

        print "data = ", data

        try:
            body = self._send(data)
        except (IOError, LicenseException) as ex:
            self.server.log.debug(
                    "license send exception failed with status %s", ex)

            self._callfailed(str(ex))
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
            self.server.log.debug("phone home failed with status %d",
                                                            conn.getcode())
            raise LicenseException("Failed with status " + str(conn.getcode))

        reply = json.loads(reply_json)

        return reply

    def _callfailed(self, info):
        session = meta.Session()

        data = {}

        entry = Domain.getone()
        if not entry.contact_failures:
            entry.contact_failures = 1
        else:
            entry.contact_failures += 1
        session.commit()

        if entry.contact_time:
#            print "contact_time:", entry.contact_time
#            print "timestamp thing:", datetime.datetime.now()
            silence_time = (datetime.datetime.now() - \
                            entry.contact_time).total_seconds()
            if silence_time <= self.MAX_SILENCE_TIME:
                self.server.log.debug("Silence time: %d <= max of: %d",
                                            silence_time, self.MAX_SILENCE_TIME)
                return
            data['failure_hours'] = \
                    int((datetime.datetime.now() - \
                        entry.contact_time).total_seconds() / 3600)
        else:
            # 0 means never connected.
            # Could happen when the controller is running, but
            # the firewall isn't configured yet.
            data['failure_hours'] = 0

        self.server.log.debug("failure hours was longer than: %d : %d",
                              self.MAX_SILENCE_TIME, data['failure_hours'])

        notification = self.server.notifications.get("phonehome")
        notification.description = info

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
