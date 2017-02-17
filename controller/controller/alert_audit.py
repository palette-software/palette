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
    def invalidate_previous(cls, session, alert_type, process_name):
        prev_setting = session.query(cls) \
            .filter(cls.alert_type == alert_type) \
            .filter(cls.process_name == process_name) \
            .order_by(cls.valid_from.desc()) \
            .first()
        if prev_setting is not None:
            prev_setting.valid_to = func.now()  # Need to be in same transaction as session.add

    @classmethod
    def log(cls, session, entry, userid, alert_type, setting):
        """
        Create a new record in the audit table when there is a change in the settings.
        The audit record contains the new values and the timestamp of the change.

        :param session: The same session in which the new settings are commited to the DB
        :param entry: The previous values of the setting
        :param userid: The user who is currently logged in
        :param alert_type: Either cpu or memory
        :param setting: The new setting values
        :return: None
        """
        # pylint: disable=too-many-arguments

        # setting might not contain alert_type
        setting["alert_type"] = alert_type

        if cls.has_changes(setting, entry):
            cls.invalidate_previous(session, alert_type, setting['process_name'])

            audit_log = cls(userid=userid, **setting)
            session.add(audit_log)  # Need to be in same transaction as prev_setting.valid_to
