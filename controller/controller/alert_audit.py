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

    @classmethod
    def invalidate_previous(cls, session, alert_type, process_name):
        prev_setting = session.query(cls) \
            .filter(cls.alert_type == alert_type) \
            .filter(cls.process_name == process_name) \
            .order_by(cls.valid_from.desc()) \
            .first()
        if prev_setting is not None:
            # Need to be in same transaction as session.add, otherwise it is not
            # guaranteed that func.now() will return the very same timestamp
            prev_setting.valid_to = func.now()

    @classmethod
    def log_setting_change(cls, session, userid, alert_type, setting):
        """
        Create a new record in the audit table. The audit record contains the new values
        and the timestamp of the change.

        :param session: The same session in which the new settings are commited to the DB
        :param userid: The user who is currently logged in
        :param alert_type: Either cpu or memory
        :param setting: The new setting values
        :return: None
        """

        # setting might not contain alert_type
        setting["alert_type"] = alert_type

        cls.invalidate_previous(session, alert_type, setting['process_name'])

        audit_log = cls(userid=userid, **setting)
        session.add(audit_log)  # Need to be in same transaction as prev_setting.valid_to
