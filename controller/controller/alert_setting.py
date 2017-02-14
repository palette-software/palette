import akiri.framework.sqlalchemy as meta
from sqlalchemy import Column, String, Integer, BigInteger

from alert_audit import AlertAudit
from mixin import BaseMixin, BaseDictMixin


# pylint: disable=line-too-long
def _value_with_key(obj, key):
    return obj[key] if key in obj else None

class AlertSetting(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = 'alert_settings'

    ALERTING_DISABLED_VALUE = None
    CPU = 'cpu'
    MEMORY = 'memory'

    process_name = Column(String, nullable=False, primary_key=True)
    alert_type = Column(String, nullable=False, primary_key=True)
    threshold_warning = Column(BigInteger, default=ALERTING_DISABLED_VALUE)
    threshold_error = Column(BigInteger, default=ALERTING_DISABLED_VALUE)
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
        cls.fill_defaults(cls.CPU)
        cls.fill_defaults(cls.MEMORY)

    @classmethod
    def fill_defaults(cls, alert_type):
        for process in cls.valid_process_names:
            row = {'process_name': process, 'alert_type': alert_type}
            cls.defaults.append(row)

    @classmethod
    def is_threshold_enabled(cls, value):
        return value != cls.ALERTING_DISABLED_VALUE

    @classmethod
    def get_all(cls, alert_type):
        result = meta.Session.query(cls) \
            .filter(cls.alert_type == alert_type) \
            .all()
        return [record.todict() for record in result]

    @classmethod
    def get_monitored(cls, alert_type):
        result = meta.Session.query(cls.process_name) \
            .filter(cls.is_threshold_enabled(cls.threshold_warning) | \
                cls.is_threshold_enabled(cls.threshold_error)) \
            .filter(cls.alert_type == alert_type)
        return [record.process_name for record in result]

    @classmethod
    def update_all(cls, values, alert_type, userid):
        session = meta.Session()
        for d in values:
            entry = session.query(cls) \
                    .filter(cls.alert_type == alert_type) \
                    .filter(cls.process_name == d['process_name']) \
                    .one()
            AlertAudit.log(session, entry, userid, alert_type, d)
            entry.threshold_warning = _value_with_key(d, 'threshold_warning')
            entry.threshold_error = _value_with_key(d, 'threshold_error')
            entry.period_warning = _value_with_key(d, 'period_warning')
            entry.period_error = _value_with_key(d, 'period_error')

        session.commit()
