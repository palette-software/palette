import datetime
import logging
import time

import akiri.framework.sqlalchemy as meta
from event_control import EventControl
from manager import Manager
from sqlalchemy import Column, BigInteger, Float, String, DateTime, func
from sqlalchemy.schema import ForeignKey
from system import SystemKeys

logger = logging.getLogger()


class MetricEntry(meta.Base):
    # pylint: disable=no-init
    __tablename__ = "metrics"

    metricid = Column(BigInteger, unique=True, nullable=False,
                      autoincrement=True, primary_key=True)

    agentid = Column(BigInteger,
                     ForeignKey("agent.agentid", ondelete='CASCADE'),
                     nullable=False)

    cpu = Column(Float)
    memory = Column(Float)
    process_name = Column(String)
    creation_time = Column(DateTime, server_default=func.now())


class MetricManager(Manager):
    def add(self, agent, process_name, cpu, memory):
        session = meta.Session()

        entry = MetricEntry(agentid=agent.agentid, process_name=process_name,
                            cpu=cpu, memory=memory)
        session.add(entry)
        session.commit()

    def prune(self):
        """Prune/remove old rows from the metrics table."""

        metric_save_days = self.system[SystemKeys.METRIC_SAVE_DAYS]
        logger.debug("metrics: prune save %d days", metric_save_days)

        stmt = ("DELETE FROM metrics " + \
                "WHERE creation_time < NOW() - INTERVAL '%d DAYS'") % \
               (metric_save_days,)

        connection = meta.get_connection()
        result = connection.execute(stmt)
        connection.close()

        logger.debug("metrics: pruned %d rows", result.rowcount)
        return {'status': "OK", 'pruned': result.rowcount}

    def check(self, metric='cpu'):
        # pylint: disable=too-many-locals
        if metric != 'cpu':
            return {'error': 'Unknown metric: %s' % metric}

        cpu_load_warn = self.system[SystemKeys.CPU_LOAD_WARN]
        cpu_load_error = self.system[SystemKeys.CPU_LOAD_ERROR]
        cpu_period_warn = self.system[SystemKeys.CPU_PERIOD_WARN]
        cpu_period_error = self.system[SystemKeys.CPU_PERIOD_ERROR]

        connection = meta.get_connection()

        results = []

        agents = self.server.agentmanager.all_agents()
        for key in agents.keys():
            agent = agents[key]

            self.process_level_check(agent, connection, 'cpu')
            self.process_level_check(agent, connection, 'memory')

            error_report = self._cpu_above_threshold(connection,
                                                     agent, cpu_load_error,
                                                     cpu_period_error)
            logger.debug("metrics: error_report '%s': %s",
                         agent.displayname, str(error_report))

            if error_report['above'] != 'yes':
                warn_report = self._cpu_above_threshold(connection,
                                                        agent, cpu_load_warn,
                                                        cpu_period_warn)

                logger.debug("metrics: warn_report '%s': %s",
                             agent.displayname, str(warn_report))
                if error_report['above'] == 'unknown' and \
                                warn_report['above'] == 'unknown':
                    results.append({"displayname": agent.displayname,
                                    "status": "unknown",
                                    "info": ("No data yet: " + \
                                             "error/warning %d/%d seconds") % \
                                            (cpu_period_error, cpu_period_warn)})
                    continue

            if error_report['above'] == 'yes':
                color = 'red'
                report_value = error_report['value']
                description = "%d > %d" % (report_value, cpu_load_error)
            elif warn_report['above'] == 'yes':
                color = 'yellow'
                report_value = warn_report['value']
                description = "%d > %d" % (report_value, cpu_load_warn)
            else:
                color = 'green'
                if error_report['above'] != 'unknown':
                    report_value = error_report['value']
                else:
                    report_value = warn_report['value']
                description = "%d" % report_value

            result = self._report('cpu', connection, agent, color,
                                  report_value, description, None,
                                  cpu_load_error, cpu_load_warn,
                                  cpu_period_error / 60, cpu_period_warn / 60)
            results.append(result)

        connection.close()

        if not len(results):
            return {'status': 'OK', 'info': 'No agents connected.'}
        return {'status': 'OK', 'info': results}

    def process_level_check(self, agent, connection, metric_type):
        # pylint: disable = too-many-locals
        stmt = """
            select
                    process_name,
                    min(threshold_warning) as threshold_warning,
                    min(threshold_error) as threshold_error,
                    min(period_warning) as period_warning,
                    min(period_error) as period_error,
                    min(value_warning) as value_warning,
                    min(value_error) as value_error,
                    min(color) as color
            FROM
                    (
                            SELECT
                                    process_name,
                                    CASE WHEN level = 'warning'
                                            THEN threshold END   AS threshold_warning,
                                    CASE WHEN level = 'error'
                                            THEN threshold END   AS threshold_error,
                                    CASE WHEN level = 'warning'
                                            THEN period END      AS period_warning,
                                    CASE WHEN level = 'error'
                                            THEN period END      AS period_error,
                                    CASE WHEN level = 'warning'
                                            THEN average_value END AS value_warning,
                                    CASE WHEN level = 'error'
                                            THEN average_value END AS value_error,
                                    color
                            FROM (
                                    SELECT
                                            name,
                                            process_name,
                                            threshold,
                                            period,
                                            level,
                                            avg(value) as average_value
                                    FROM (
                                            SELECT
                                                    '%(metric_type)s_' || config.process_name AS name,
                                                    config.process_name,
                                                    config.threshold,
                                                    config.period,
                                                    config.level,
                                                    creation_time,
                                                    %(metric_type)s as value
                                            FROM
                                                    (SELECT
                                                             process_name,
                                                             threshold_warning AS threshold,
                                                             period_warning    AS period,
                                                             'warning'         AS level
                                                     FROM alert_settings
                                                     WHERE 1 = 1
                                                             AND threshold_warning IS NOT NULL
                                                             AND period_warning > 0
                                                             AND alert_type = '%(metric_type)s'
                                                     UNION ALL
                                                     SELECT
                                                             process_name,
                                                             threshold_error AS threshold,
                                                             period_error    AS period,
                                                             'error'         AS level
                                                     FROM alert_settings
                                                     WHERE 1 = 1
                                                             AND threshold_error IS NOT NULL
                                                             AND period_error > 0
                                                             AND alert_type = '%(metric_type)s'
                                                    ) config
                                                    LEFT JOIN metrics m
                                                            ON m.process_name = config.process_name
                                                            AND m.creation_time >= NOW() - (config.period * '1 minutes' :: INTERVAL)
                                                            AND m.agentid = %(agentid)d
                                    ) details
                                             GROUP BY
                                                     name, process_name, threshold, period, level
                                     ) current
                                    LEFT JOIN notifications n
                                            ON n.name = current.name
                    ) process_level_details
            group by process_name
        """ % {'metric_type': metric_type, 'agentid': agent.agentid}

        result = connection.execute(stmt)
        for row in result:
            if row[0] != None:
                process_name = row[0]

                def get_as_int_or_none(value):
                    return value is not None and int(round(value, 0)) or None

                threshold_warning = get_as_int_or_none(row[1])
                threshold_error = get_as_int_or_none(row[2])
                period_warning = get_as_int_or_none(row[3])
                period_error = get_as_int_or_none(row[4])

                # These two can be null
                value_warning = row[5]
                value_error = row[6]

                current_color = row[7]

                def is_over_threshold(period, threshold, current_value):
                    return (period is not None and threshold is not None) \
                           and current_value is not None and current_value >= threshold

                description = ''
                if is_over_threshold(period_error, threshold_error, value_error) \
                        and current_color != 'red':
                    average_value = value_error
                    color = 'red'
                    description = "%d > %d" % (value_error, threshold_error)
                elif is_over_threshold(period_warning, threshold_warning, value_warning) \
                        and not is_over_threshold(period_error, threshold_error, value_error) \
                        and current_color != 'yellow':
                    average_value = value_warning
                    color = 'yellow'
                    description = "%d > %d" % (value_warning, threshold_warning)
                elif not is_over_threshold(period_warning, threshold_warning, value_warning) \
                        and not is_over_threshold(period_error, threshold_error, value_error) \
                        and current_color != 'green':
                    average_value = value_warning is not None and value_warning or value_error
                    color = 'green'
                else:
                    continue

                if average_value is None:
                    continue

                self._report(metric_type, connection, agent, color, average_value, description, process_name,
                             threshold_error, threshold_warning, period_error, period_warning)

    def _report(self, metric, connection, agent, color, report_value,
                description, process, threshold_error, threshold_warning,
                period_error, period_warning):
        # pylint: disable=too-many-arguments
        """
            Generates an event, if appropriate and updates the
            relevant notification row.

            Arguments:
                text name used for the notifications table and
                debug messages.

            Returns a dictionary for the report.
        """
        name = metric
        if process:
            name = name + '_' + process

        notification = self.server.notifications.get(name, agent.agentid)

        if color != notification.notified_color:
            if color != 'green' or \
                    (color == 'green' and notification.notified_color):
                self._gen_event(metric, agent, color, report_value, process,
                                threshold_error, threshold_warning, period_error, period_warning)

                stmt = ("UPDATE notifications " + \
                        "SET color='%s', notified_color='%s', " +
                        "description='%s'" + \
                        "WHERE notificationid=%d") % \
                       (color, color, description, notification.notificationid)

                connection.execute(stmt)

        return {"displayname": agent.displayname,
                "status": color,
                "value": report_value}

    def _cpu_above_threshold(self, connection, agent, threshold, period):
        """Checks the data for the last "period" seconds.
           If the most recent sample does not include data for
           more than "period" seconds, then return "status": "no" since
           the data is too new.

           Otherwise, if the average of the samples is below the threshold,
           then return "no" or if the average of the samples is above
           or equal to the threshold, then return "yes".

           Returns a dictionary:
                above: 'yes', 'no' or 'unknown'
                value: the average, if 'above' value is not 'unknown'
        """

        logger.debug("metrics: _cpu_above_threshold '%s', " + \
                     "threshold %d, period %d",
                     agent.displayname, threshold, period)
        if not agent.last_connection_time:
            logger.error("metrics: no last_connection_time for '%s'",
                         agent.displayname)
            return {"above": "unknown"}

        # Seconds since the epoch
        last_connection_time = (agent.last_connection_time -
                                datetime.datetime.utcfromtimestamp(0)). \
            total_seconds()

        if time.time() - last_connection_time < period:
            # The agent hasn't been connected at least "period" amount
            # of time.
            logger.debug("metrics: too short connection: %d - %d < %d = %d",
                         time.time(), last_connection_time, period,
                         time.time() - last_connection_time)
            return {"above": "unknown"}

        stmt = ("SELECT AVG(cpu) FROM metrics WHERE " + \
                "agentid = %d AND " + \
                "process_name = '_Total' AND " + \
                "creation_time >= NOW() - INTERVAL '%d seconds'") % \
               (agent.agentid, period)

        report_value = -1
        result = connection.execute(stmt)
        for row in result:
            if row[0] == None:
                report_value = -1
            else:
                report_value = int(round(row[0], 0))

        logger.debug("metrics: '%s' threshold: %d, average: %d",
                     agent.displayname, threshold, report_value)

        if report_value == -1:
            logger.debug("metrics: No samples for agent '%s'.",
                         agent.displayname)
            return {"above": "unknown"}
        elif report_value < threshold:
            return {"above": "no", "value": report_value}
        else:
            return {"above": 'yes', "value": report_value}

    def _gen_event(self, which, agent, color, value, process,
                   threshold_error, threshold_warning, period_error, period_warning):
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-branches
        data = agent.todict()

        if not process:
            if color == 'green':
                event = EventControl.CPU_LOAD_OKAY
            elif color == 'yellow':
                event = EventControl.CPU_LOAD_ABOVE_LOW_WATERMARK
            elif color == 'red':
                event = EventControl.CPU_LOAD_ABOVE_HIGH_WATERMARK
            else:
                logger.error("_gen_event: Invalid color: %s", color)
                return
        else:
            if which == 'cpu':
                data['process_name'] = process
                if color == 'green':
                    event = EventControl.CPU_LOAD_PROCESS_OKAY
                elif color == 'yellow':
                    event = EventControl.CPU_LOAD_PROCESS_ABOVE_LOW_WATERMARK
                elif color == 'red':
                    event = EventControl.CPU_LOAD_PROCESS_ABOVE_HIGH_WATERMARK
                else:
                    logger.error("_gen_event: Invalid color: %s", color)
                    return
            elif which == 'memory':
                value = value / (1024 * 1024)
                data['process_name'] = process
                if color == 'green':
                    event = EventControl.MEMORY_PROCESS_OKAY
                elif color == 'yellow':
                    event = EventControl.MEMORY_PROCESS_ABOVE_LOW_WATERMARK
                elif color == 'red':
                    event = EventControl.MEMORY_PROCESS_ABOVE_HIGH_WATERMARK
                else:
                    logger.error("_gen_event: Invalid color: %s", color)
                    return
            else:
                logger.error("_gen_event: Invalid event type: %s", which)
                return


        data["threshold_error"] = threshold_error
        data["threshold_warning"] = threshold_warning
        data["period_error"] = period_error
        data["period_warning"] = period_warning
        data["cpu"] = int(value)
        data["info"] = "%s: %d" % (which.title(), value)
        self.server.event_control.gen(event, data)
