import akiri.framework.sqlalchemy as meta
from sqlalchemy import Column, String, Integer

from mixin import BaseMixin, BaseDictMixin


# pylint: disable=line-too-long


class AlertSetting(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = 'alert_settings'

    ALERTING_DISABLED_VALUE = None

    process_name = Column(String, nullable=False, primary_key=True)
    alert_type = Column(String, nullable=False, primary_key=True)
    threshold_warning = Column(Integer, default=ALERTING_DISABLED_VALUE)
    threshold_error = Column(Integer, default=ALERTING_DISABLED_VALUE)
    period_warning = Column(Integer, default=60)
    period_error = Column(Integer, default=60)

    valid_process_names = ['7z', 'backgrounder', 'clustercontroller', 'dataserver', 'filestore', 'httpd', 'postgres'
        , 'redis-server', 'searchserver', 'tabadmin', 'tabadminservice', 'tabadmsvc', 'tabadmwrk'
        , 'tabcmd', 'tableau', 'tabprotosrv', 'tabrepo', 'tabspawn', 'tabsvc', 'tabsystray'
        , 'tdeserver', 'tdeserver64', 'vizportal', 'vizqlserver', 'wgserver', 'zookeeper']

    defaults = []

    @classmethod
    def prepare(cls):
        # Make sure that defaults are clear
        cls.defaults = []
        # Prepare the defaults
        cls.fill_defaults('cpu')
        cls.fill_defaults('memory')

    @classmethod
    def fill_defaults(cls, alert_type):
        for process in cls.valid_process_names:
            row = {'process_name': process, 'alert_type': alert_type}
            cls.defaults.append(row)

    @classmethod
    def is_threshold_enabled(cls, value):
        return value != cls.ALERTING_DISABLED_VALUE

    @classmethod
    def get_all_cpu(cls):
        result = meta.Session.query(cls) \
            .filter(cls.alert_type == 'cpu') \
            .all()

        return [record.todict() for record in result]

    @classmethod
    def get_all_memory(cls):
        result = meta.Session.query(cls) \
            .filter(cls.alert_type == 'memory') \
            .all()

        return [record.todict() for record in result]

    @classmethod
    def get_monitored(cls):
        result = meta.Session.query(cls.process_name).filter(
            (cls.is_threshold_enabled(cls.threshold_warning) | cls.is_threshold_enabled(cls.threshold_error))
        )
        return [record.process_name for record in result]

    @classmethod
    def update_all_cpu(cls, values):
        session = meta.Session()
        for d in values:
            session.query(cls) \
                .filter(cls.alert_type == 'cpu') \
                .filter(cls.process_name == d['process_name']) \
                .update(d)
        session.commit()

    @classmethod
    def update_all_memory(cls, values):
        session = meta.Session()
        for d in values:
            session.query(cls) \
                .filter(cls.alert_type == 'memory') \
                .filter(cls.process_name == d['process_name']) \
                .update(d)
        session.commit()
