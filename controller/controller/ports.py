import threading

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy import Boolean
from sqlalchemy.schema import ForeignKey

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from agent import Agent
from event_control import EventControl
from manager import Manager
from mixin import BaseMixin

class PortEntry(meta.Base, BaseMixin):
    __tablename__ = "ports"

    portid = Column(BigInteger, unique=True, nullable=False,
                             autoincrement=True, primary_key=True)

    envid = Column(BigInteger, ForeignKey("environment.envid"))


    dest_host = Column(String, nullable=False)  # host to check
    dest_port = Column(Integer, nullable=False)  # port to check
    service_name = Column(String, nullable=False)  # user editable
    agentid = Column(BigInteger, ForeignKey("agent.agentid"),
                                                     nullable=False)
    color = Column(String)   # red or green
    notified_color = Column(String) # red or green

    max_time = Column(Integer)
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
        self.log = server.log

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

            state = self.check_port(port)
            report.append({'state': state,
                           'dest-host': port.dest_host,
                           'dest-port': port.dest_port,
                           'service-name': port.service_name,
                           'agentid': port.agentid})

        return {'status': 'OK', 'ports': report}

    def check_port(self, entry):
        """Tests connectivity from an agent to a host/port.
           Returns "success", "fail", or "unknown" (if agent
           isn't connected)."""

        agent = self.server.agentmanager.agent_by_agentid(entry.agentid)
        if not agent:
            self.log.debug(
                "check_port: agentid %d not connected.  Will not " + \
                "check service_name %s dest_host '%s' dest_port '%d'",
                entry.agentid, entry.service_name, entry.dest_host,
                entry.dest_port)
            return "unknown"

        command = "pok %s %d" % (entry.dest_host, entry.dest_port)

        body = self.server.cli_cmd(command, agent)
        data = agent.todict()
        data['service_name'] = entry.service_name
        data['dest_port'] = entry.dest_port
        data['dest_hostname'] = entry.dest_host

        if body['exit-status']:
            self.log.info(
                "Connection to '%s' failed: host '%s', port %d)",
                       entry.service_name, entry.dest_host, entry.dest_port)

            color = 'red'
        else:
            color = 'green'

        # generate an event if appropriate
        if color == 'red' and entry.notified_color != 'red':
            data['error'] = "Connection to '%s' failed: host '%s', port %d" % \
                       (entry.service_name, entry.dest_host, entry.dest_port)

            self.server.event_control.gen(EventControl.PORT_CONNECTION_FAILED,
                                          data)
        elif entry.notified_color == 'red' and color == 'green':
            data['info'] = \
                    "Connection to '%s' is now okay: host '%s', port %d" % \
                    (entry.service_name, entry.dest_host, entry.dest_port)

            self.server.event_control.gen(EventControl.PORT_CONNECTION_OKAY,
                                          data)

        meta.Session.query(PortEntry).\
            filter(PortEntry.portid == entry.portid).\
            update({'color': color, 'notified_color': color},
                   synchronize_session=False)

        meta.Session.commit()

        if body['exit-status']:
            return 'fail'
        else:
            return 'success'

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

