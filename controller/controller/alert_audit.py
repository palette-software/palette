import akiri.framework.sqlalchemy as meta
from sqlalchemy import Column, String, Integer, BigInteger, DateTime, ForeignKey
from sqlalchemy import func


class AlertAudit(meta.Base):
    __tablename__ = 'alert_audit'

    id = Column(BigInteger, unique=True, nullable=False,
                autoincrement=True, primary_key=True)
    userid = Column(BigInteger, ForeignKey("users.userid"), nullable=False)
    process_name = Column(String, nullable=False)
    alert_type = Column(String, nullable=False)
    threshold_warning = Column(BigInteger)
    threshold_error = Column(BigInteger)
    period_warning = Column(Integer)
    period_error = Column(Integer)
    valid_from = Column(DateTime, server_default=func.now())
    valid_to = Column(DateTime)

    @staticmethod
    def has_changes(setting, entry):
        for key in setting:
            if setting[key] != getattr(entry, key):
                return True
        return False

    @classmethod
    def log(cls, session, entry, userid, alert_type, setting):
        setting["alert_type"] = alert_type
        if cls.has_changes(setting, entry):
            audit_log = cls(userid=userid, **setting)

            # Update the corresponding 'valid to' column as well
            prev_setting = session.query(cls).filter(cls.alert_type == alert_type) \
                                             .filter(cls.process_name == setting['process_name']) \
                                             .filter(cls.id != audit_log.id) \
                                             .order_by(cls.valid_from.desc()) \
                                             .first()
            session.add(audit_log)
            if prev_setting is None:
                # There is no previous modification on this setting
                return

            prev_setting.valid_to = audit_log.valid_from
