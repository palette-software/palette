from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy import Integer, BigInteger, SmallInteger
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import not_

from akiri.framework.ext.sqlalchemy import meta

class Site(meta.Base):
    __tablename__ = 'sites'

    siteid = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    status = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    user_quota = Column(Integer)
    content_admin_mode = Column(Integer)
    storage_quota = Column(BigInteger)
    metrics_level = Column(SmallInteger)
    status_reason = Column(String)
    subscriptions_enabled = Column(Boolean, nullable=False)
    custom_subscription_footer = Column(String)
    custom_subscription_email = Column(String)
    luid = Column(String, unique=True)
    query_limit = Column(Integer)

    @classmethod
    def get(cls, siteid):
        try:
            entry = meta.Session.query(Site).\
                filter(Site.siteid == siteid).one()
        except NoResultFound, e:
            entry = None
        return entry

    @classmethod
    def all(cls):
        return meta.Session.query(Site).order_by(Site.name).all()

    @classmethod
    def load(cls, agent):
        stmt = \
            'SELECT id, name, status, created_at, updated_at, ' +\
            'user_quota, content_admin_mode, storage_quota, metrics_level, '+\
            'status_reason, subscriptions_enabled, ' +\
            'custom_subscription_footer, custom_subscription_email, '+\
            'luid, query_limit ' +\
            'FROM sites'

        data = agent.odbc.execute(stmt)
        ids = []

        session = meta.Session()
        for row in data['']:
            entry = Site.get(row[0])
            if not entry:
                entry = Site(siteid=row[0])
            entry.name = row[1]
            entry.status = row[2]
            entry.created_at = row[3]
            entry.updated_at = row[4]
            entry.user_quota = row[5]
            entry.content_admin_mode = row[6]
            entry.storage_quota = row[7]
            entry.metrics_level = row[8]
            entry.status_reason = row[9]
            entry.subscriptions_enabled = row[10]
            entry.custom_subscription_footer = row[11]
            entry.custom_subscription_email = row[12]
            entry.luid = row[13]
            entry.query_limit = row[14]
            session.merge(entry)
            ids.append(entry.siteid)

        session.query(Site).\
            filter(not_(Site.siteid.in_(ids))).\
            delete(synchronize_session='fetch')

        session.commit()

        d = {u'status': 'OK', u'count': len(data[''])}
        return d
