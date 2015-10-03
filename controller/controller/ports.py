import logging
import threading
import json

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy import Boolean, Float
from sqlalchemy.schema import ForeignKey

import akiri.framework.sqlalchemy as meta

from agent import Agent
from event_control import EventControl
from manager import Manager
from mixin import BaseMixin
from util import failed

logger = logging.getLogger()

class PortEntry(meta.Base, BaseMixin):
    __tablename__ = "ports"

    portid = Column(BigInteger, unique=True, nullable=False,
                             autoincrement=True, primary_key=True)

    envid = Column(BigInteger, ForeignKey("environment.envid"))


    dest_host = Column(String, nullable=False)  # host to check
    dest_port = Column(Integer, nullable=False)  # port to check
    service_name = Column(String, nullable=False)  # user editable
    agentid = Column(BigInteger,
                     ForeignKey("agent.agentid", ondelete='CASCADE'),
                     nullable=False)
    ip_address = Column(String)
    connect_time = Column(Float)
    max_time = Column(Integer, default=60, nullable=False)

    color = Column(String)   # red or green
    notified_color = Column(String) # red or green

    active = Column(Boolean, default=True)

    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(), \
                               server_onupdate=func.current_timestamp())

    # Can do this only if there is a populated database with agentid 1.

    # example
    # defaults = [
    #        {
    #            "envid":1,
    #            "dest_host": "localhost",
    #            "dest_port": 80,
    #            'service_name': "Localhost port 80",
    #            'agentid': 1
    #        },
    #        {
    #            "envid":1,
    #            "dest_host": "192.168.2.13",
    #            "dest_port": 3000,
    #            'service_name': "azul test service",
    #            'agentid': 1
    #        },
    #]

class PortManager(Manager):

    def __init__(self, server):
        super(PortManager, self).__init__(server)

        # A lock to allow only one port check to be done at a time.
        # Otherwise: 1) We can send the same 'failed to connect' event
        # from two separate threads (though we could make the lock
        # around just the check-event/send-event code) and 2) We don't
        # really want multiple threads checking the same ports at the
        # same time.
        self.port_lock_obj = threading.RLock()

    def check_ports_lock(self, blocking=False):
        return self.port_lock_obj.acquire(blocking)

    def check_ports_unlock(self):
        self.port_lock_obj.release()

    def check_ports(self):
        ports = PortManager.find_by_envid(self.envid)

        report = []
        for port in ports:
            if port.active == False:
                # update color and notified_color to neutral
                meta.Session.query(PortEntry).\
                    filter(PortEntry.portid == port.portid).\
                    update({'color': None, 'notified_color': None},
                           synchronize_session=False)

                meta.Session.commit()
                continue

            results_dict = self.check_port(port)

            report.append(results_dict)

        return {'status': 'OK', 'ports': report}

    def check_port(self, entry):
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        """Tests connectivity from an agent to a host/port.
           Returns "success", "fail", or "unknown" (if agent
           isn't connected)."""

        details = {
                    'service_name': entry.service_name,
                    'dest_port': entry.dest_port,
                    'dest_hostname': entry.dest_host
                   }

        if entry.max_time:
            details['max_time'] = entry.max_time

        agent = self.server.agentmanager.agent_by_agentid(entry.agentid)
        if not agent:
            logger.debug("check_port: agentid %d not connected.  Will not " + \
                         "check service_name %s dest_host '%s' dest_port '%d'",
                         entry.agentid, entry.service_name, entry.dest_host,
                         entry.dest_port)
            details['error'] = \
                "agent %d not connected.  Can't do port check." % entry.agentid
            return details

        command = "pok %s %d" % (entry.dest_host, entry.dest_port)

        body = self.server.cli_cmd(command, agent, timeout=60*5)
        data = agent.todict()

        if failed(body):
            logger.error(
                "check_port: agentid %d command '%s' for service '%s' " + \
                "failed: %s",
                entry.agentid, command, entry.service_name,
                body['error'])
            details['error'] = body['error']

        if not 'exit-status' in body:
            logger.error(
                "check_port: agentid %d command '%s' for service '%s' " + \
                "did not have 'exit-status' in returned body: %s",
                entry.agentid, command, entry.service_name,
                str(body))
            details['error'] = 'Missing exit-status from port check.'
            return dict(data.items() + details.items())

        if 'stdout' in body:
            try:
                stdout = json.loads(body['stdout'])
            except ValueError as ex:
                logger.error("check_port: Bad json in stdout: %s: %s\n",
                             str(ex), body['stdout'])
                stdout = {}

            if 'milliseconds' in stdout:
                try:
                    details['connect_time'] = stdout['milliseconds']/1000.
                except TypeError as ex:
                    logger.error("check_port: Bad milliseconds value: %s: %s\n",
                                 str(ex), str(stdout))

            if 'ip' in stdout:
                details['ip'] = stdout['ip']

            if failed(stdout):
                details['error'] = stdout['error']

        if body['exit-status'] or failed(details):
            # Non-zero exit status means failure to connect or
            # resolve hostname.
            if not 'error' in details:
                details['error'] = \
                        "Connection to '%s' failed: host '%s', port %d" % \
                       (entry.service_name, entry.dest_host, entry.dest_port)
            logger.debug(details)
        elif entry.max_time and 'connect_time' in details and \
                                details['connect_time'] > entry.max_time:
            details['error'] = ("Connection time (%.1f) exceeded maximum " + \
                       "allowed (%d.0) to '%s': host '%s', port %d") % \
                       (details['connect_time'], entry.max_time,
                       entry.service_name, entry.dest_host, entry.dest_port)
            logger.debug(details)

        if failed(details):
            color = 'red'
        else:
            color = 'green'

        # Generate an event if appropriate
        if color == 'red' and entry.notified_color != 'red':
            self.server.event_control.gen(EventControl.PORT_CONNECTION_FAILED,
                                          dict(data.items() + details.items()))
        elif entry.notified_color == 'red' and color == 'green':
            data['info'] = \
                    "Connection to '%s' is now okay: host '%s', port %d" % \
                    (entry.service_name, entry.dest_host, entry.dest_port)
            self.server.event_control.gen(EventControl.PORT_CONNECTION_OKAY,
                                          dict(data.items() + details.items()))

        # Update the row
        update_dict = {'color': color, 'notified_color': color}
        if 'connect_time' in details:
            update_dict['connect_time'] = details['connect_time']
        if 'ip' in details:
            update_dict['ip_address'] = details['ip']

        meta.Session.query(PortEntry).\
            filter(PortEntry.portid == entry.portid).\
            update(update_dict,
                   synchronize_session=False)

        meta.Session.commit()

        return details

    def populate(self):
        agent_count = meta.Session.query(Agent).\
            filter(Agent.envid == self.envid).\
            count()

        if agent_count:
            PortEntry.populate()

    @classmethod
    def find_by_envid(cls, envid):
        """Return all port entries by envid, sorted by agentid."""
        return meta.Session.query(PortEntry).\
            filter(PortEntry.envid == envid).\
            order_by(PortEntry.agentid).\
            order_by(PortEntry.dest_port).\
            all()

