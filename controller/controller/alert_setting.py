from sqlalchemy import Column, String, Integer, Boolean

import akiri.framework.sqlalchemy as meta
from mixin import BaseMixin


class AlertSetting(meta.Base, BaseMixin):

    __tablename__ = 'alert_settings'

    process_name = Column(String, unique=True, nullable=False, primary_key=True)
    threshold_warning = Column(Integer)
    threshold_error = Column(Integer)
    period_warning = Column(Integer)
    period_error = Column(Integer)

    def __getitem__(self, key):
        query = meta.Session.query(AlertSetting)
        return query.all()
        # return self.get_all_by_keys([])
