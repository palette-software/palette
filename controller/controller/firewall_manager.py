from sqlalchemy import Column, Integer, BigInteger, String, Boolean
from sqlalchemy.schema import ForeignKey, UniqueConstraint

from akiri.framework.ext.sqlalchemy import meta

from agentmanager import AgentManager
from event_control import EventControl, EventControlManager
from mixin import BaseDictMixin

class FirewallEntry(meta.Base):
    __tablename__ = "firewall"

    firewallid = Column(BigInteger, unique=True, nullable=False,
                             autoincrement=True, primary_key=True)

    agentid = Column(BigInteger, ForeignKey("agent.agentid"),
                                                     nullable=False)

    name = Column(String)   # "HTTP", "HTTPS", etc.
    port = Column(Integer, nullable=False)  # port that needs to be open
    color = Column(String)
    status = Column(String)     # currently unused; for the future

class FirewallManager(object):

    DEFAULT_PRIMARY_PORTS = [
            {"name": "HTTP",
                "port": 80,
                "color": 'red'
            },
            {"name": "HTTPS",
                "port": 443,
                "color": 'red'
            },
    ]

    # They are the same now.  May change in the future
    DEFAULT_NON_PRIMARY_PORTS = DEFAULT_PRIMARY_PORTS

    def __init__(self, server):
        self.server = server
        self.log = server.log

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
                name="Palette Agent", port=agent.listen_port, color="red")
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

        ports = [entry.port for entry in rows]
        body = agent.firewall.enable(ports)
        success = True
        if 'error' in body:
            self.log.error(\
                ("open_firewall_ports failed to open ports '%s' on " +
                     "host %s, failed with: %s") % \
                            (str(ports), agent.displayname, body['error']))
            self.server.event_control.gen(\
                    EventControl.FIREWALL_OPEN_FAILED,
                        dict({
                            'error': body['error'], 
                            'info': "Ports: %s" % str(ports)}.items() + \
                                                    agent.__dict__.items()))
            success = False
            color = 'red'
        else:
            color = 'green'

        session.query(FirewallEntry).\
            filter(FirewallEntry.agentid == agent.agentid).\
            update({'color': color}, synchronize_session=False)

        session.commit()
        if not success:
            raise IOError("Could not open all firewall ports")

    def do_firewall_ports(self, agent):
        # Make sure the agent's firewall rows are populated in the table.
        self.init_firewall_ports(agent)

        # Open the agent's firewall ports.
        self.open_firewall_ports(agent)
