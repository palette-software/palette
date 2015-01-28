# This module is named licensing to avoid the Python reserved keyword 'license'.

import re

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

    def info(self, agent):
        """Don't do anything very active since this can run when
           in UPGRADE state, etc."""

        server = self.server
        envid = server.environment.envid

        data = {}
        entry = Domain.getone()
        data['license-key'] = entry.license_key
        data['systemid'] = entry.systemid
        data['expiration-time'] = entry.expiration_time
        data['contact-time'] = entry.contact_time
        data['trial'] = entry.trial

        data['palette-version'] = self.server.system.get(
                                        SystemConfig.PALETTE_VERSION,
                                        default='unknown')

        if not agent:
            # primary agent isn't connected, so get the older data.
            try:
                agent = meta.Session.query(Agent).\
                   filter(Agent.agent_type == AgentManager.AGENT_TYPE_PRIMARY).\
                   one()

            except NoResultFound:
                print "No primary agents ever connected."
                return data

        entry = LicenseEntry.get_by_agentid(agent.agentid)
        data['tableau-license-type'] = entry.gettype()
        data['tableau-license-interactors'] = entry.interactors
        data['tableau-license-viewers'] = entry.viewers

        data['tableau-version'] = YmlEntry.get(envid, 'version.external',
                                               default='unknown')

        data['tableau-bitness'] = YmlEntry.get(envid, 'version.bitness',
                                       default='unknown')

        data['processor-type'] = agent.processor_type
        data['processor-count'] = agent.processor_count
        data['processor-bitness'] = agent.bitness

        data['primary-uuid'] = agent.uuid

        return data
