from sqlalchemy import Column, BigInteger, Float, DateTime, func

from sqlalchemy.schema import ForeignKey

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from event_control import EventControl
from general import SystemConfig

#from event_control import EventControl

class MetricEntry(meta.Base):
    # pylint: disable=no-init
    __tablename__ = "metrics"

    metricid = Column(BigInteger, unique=True, nullable=False,
                             autoincrement=True, primary_key=True)

    agentid = Column(BigInteger, ForeignKey("agent.agentid"),
                                                     nullable=False)

    cpu = Column(Float)
    creation_time = Column(DateTime, server_default=func.now())

class MetricManager(object):

    def __init__(self, server):
        self.server = server
        self.log = server.log
        self.notifications = self.server.notifications
        self.st_config = SystemConfig(server.system)

    def add(self, agent, cpu):
        session = meta.Session()

        entry = MetricEntry(agentid=agent.agentid, cpu=cpu)
        session.add(entry)
        session.commit()

    def check(self, metric='cpu'):
        # pylint: disable=too-many-locals
        if metric != 'cpu':
            return {'error': 'Unknown metric: %s' % metric}

        try:
            cpu_load_warn = self.st_config.cpu_load_warn
            cpu_load_error = self.st_config.cpu_load_error
            cpu_load_period = self.st_config.cpu_load_period
        except ValueError as ex:
            return {'error': str(ex)}

        connection = meta.engine.connect()
        session = meta.Session()

        results = []

        agents = self.server.agentmanager.all_agents()
        for key in agents.keys():
            agent = agents[key]
            stmt = ("SELECT cpu FROM metrics WHERE " + \
                   "agentid = %d AND " + \
                   "creation_time >= NOW() - INTERVAL '%d seconds'") % \
                   (agent.agentid, cpu_load_period)

            color = None
            sample_count = 0

            report_value = 0

            for entry in connection.execute(stmt):
                sample_count += 1

                if entry[0] >= cpu_load_error:
                    color = 'red'
                    report_value = entry[0]
                    break
                elif entry[0] >= cpu_load_warn:
                    color = 'yellow'
                    report_value = entry[0]
                elif not color:
                    color = 'green'
                    report_value = entry[0]

            if not sample_count:
                self.log.debug(
                    "metrics: No samples for agent %s." % agent.displayname)
                results.append({'displayname': 'No samples'})
                continue

            # Fixme: If only 1 sample and the agent has not been
            # connected < period, then ignore.
            notification = self.notifications.get('cpu', agent.agentid)
            if color != notification.notified_color:
                if color != 'green' or \
                            (color == 'green' and notification.notified_color):
                    self._gen_event("CPU Load", agent, color, report_value)
                    notification.color = color
                    notification.notified_color = color
                    session.add(notification)
                    session.commit()

            results.append({"displayname": agent.displayname,
                            "status": color,
                            "value": report_value})

        if not len(results):
            return {'status': 'OK', 'info': 'No agents connected with data.'}
        return {'status': 'OK', 'info': results}

    def _gen_event(self, which, agent, color, value):
        if color == 'green':
            event = EventControl.CPU_LOAD_OKAY
        elif color == 'yellow':
            event = EventControl.CPU_LOAD_ABOVE_LOW_WATERMARK
        elif color == 'red':
            event = EventControl.CPU_LOAD_ABOVE_HIGH_WATERMARK
        else:
            self.log.error("_gen_event: Invalid color: %s", color)
            return

        data = agent.todict()
        data['info'] = "%s: %.1f" % (which, value)
        self.server.event_control.gen(event, data)
