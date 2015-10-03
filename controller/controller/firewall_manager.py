import logging
from sqlalchemy import Column, Integer, BigInteger, String
from sqlalchemy.schema import ForeignKey

import akiri.framework.sqlalchemy as meta

from .manager import Manager
from agentmanager import AgentManager
from event_control import EventControl

logger = logging.getLogger()

class FirewallEntry(meta.Base):
    # pylint: disable=no-init
    __tablename__ = "firewall"

    firewallid = Column(BigInteger, unique=True, nullable=False,
                             autoincrement=True, primary_key=True)

    agentid = Column(BigInteger,
                     ForeignKey("agent.agentid", ondelete='CASCADE'),
                     nullable=False)

    name = Column(String)   # "HTTP", "HTTPS", etc.
    port = Column(Integer, nullable=False)  # port that needs to be open
    color = Column(String)
    status = Column(String)     # currently unused; for the future

class FirewallManager(Manager):

    DEFAULT_PRIMARY_PORTS = [
            {"name": "HTTP",
                "port": 80,
                "color": 'green'
            },
            {"name": "HTTPS",
                "port": 443,
                "color": 'green'
            },
    ]

    # They are the same now.  May change in the future
    DEFAULT_NON_PRIMARY_PORTS = DEFAULT_PRIMARY_PORTS

    def init_firewall_ports(self, agent):
        """Make sure the agent's firewall ports have been initialized."""

        session = meta.Session()
        rows = session.query(FirewallEntry).\
            filter(FirewallEntry.agentid == agent.agentid).\
            all()

        # Already populated
        if rows:
            return

        # It was empty so add the initial default set.

        # First the listen_port
        entry = FirewallEntry(agentid=agent.agentid,
                name="Palette Agent", port=agent.listen_port, color="green")
        session.add(entry)

        # Add the others
        if agent.agent_type == AgentManager.AGENT_TYPE_PRIMARY:
            ports = FirewallManager.DEFAULT_PRIMARY_PORTS
        else:
            ports = FirewallManager.DEFAULT_NON_PRIMARY_PORTS

        for port in ports:
            entry = FirewallEntry(agentid=agent.agentid, name=port['name'],
                                port=port['port'], color=port['color'])
            session.add(entry)
        session.commit()

    def open_firewall_ports(self, agent):
        session = meta.Session()
        rows = session.query(FirewallEntry).\
            filter(FirewallEntry.agentid == agent.agentid).\
            all()

        success = True
        for entry in rows:
            port = entry.port
            body = agent.firewall.enable([port])
            if 'error' in body:
                success = False
                color = 'red'
                logging.error("open_firewall_ports failed to open port '%s' "
                              "on host %s, failed with: %s",
                              str(port), agent.displayname, body['error'])

                if entry.color != 'red':
                    data = agent.todict()
                    data['error'] = body['error']
                    data['info'] = "Port: " + str(port)
                    self.server.event_control.gen(
                        EventControl.FIREWALL_OPEN_FAILED, data)
            else:
                color = 'green'
                if entry.color == 'red':
                    data = agent.todict()
                    data['info'] = "Port: " + str(port)
                    self.server.event_control.gen(
                        EventControl.FIREWALL_OPEN_OKAY, data)

            session.query(FirewallEntry).\
                filter(FirewallEntry.agentid == agent.agentid).\
                filter(FirewallEntry.port == port).\
                update({'color': color}, synchronize_session=False)

            session.commit()

        if not success:
            raise IOError("Could not open all firewall ports")

    def do_firewall_ports(self, agent):
        # Make sure the agent's firewall rows are populated in the table.
        self.init_firewall_ports(agent)

        # Open the agent's firewall ports.
        self.open_firewall_ports(agent)
