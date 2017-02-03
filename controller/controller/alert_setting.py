from sqlalchemy import Column, String, Integer, Boolean

import akiri.framework.sqlalchemy as meta
from mixin import BaseDictMixin


class AlertSetting(meta.Base, BaseDictMixin):
    __tablename__ = 'alert_settings'

    process_name = Column(String, unique=True, nullable=False, primary_key=True)
    threshold_warning = Column(Integer)
    threshold_error = Column(Integer)
    period_warning = Column(Integer)
    period_error = Column(Integer)

    @classmethod
    def getall(cls):
        return meta.Session.query(cls).all()
