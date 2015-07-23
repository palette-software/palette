from sqlalchemy import Column, String, DateTime, Boolean, Integer, BigInteger
from sqlalchemy import not_, UniqueConstraint
from sqlalchemy.schema import ForeignKey

import akiri.framework.sqlalchemy as meta

from mixin import BaseMixin
from odbc import ODBC

class DataSource(meta.Base, BaseMixin):

    __tablename__ = 'datasources'

    dsid = Column(BigInteger, primary_key=True)
    envid = Column(Integer, ForeignKey("environment.envid"), nullable=False)
    id = Column(Integer, nullable=False)
    name = Column(String)
    repository_url = Column(String)
    owner_id = Column(Integer, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    project_id = Column(Integer)
    size = Column(BigInteger)
    lock_version = Column(Integer)
    state = Column(String)
    db_class = Column(String)
    db_name = Column(String)
    table_name = Column(String)
    site_id = Column(Integer)
    revision = Column(String)
    repository_data_id = Column(BigInteger)
    repository_extract_data_id = Column(BigInteger)
    embedded = Column(String)
    incremental_extracts = Column(Boolean)
    refreshable_extracts = Column(Boolean)
    data_engine_extracts = Column(Boolean)
    extracts_refreshed_at = Column(DateTime)

    # Added in 1.5:
    first_published_at = Column(DateTime)
    connectable = Column(Boolean)
    is_hierarchical = Column(Boolean)
    extracts_incremented_at = Column(DateTime)

    luid = Column(String)
    asset_key_id = Column(Integer)
    document_version = Column(String)

    __table_args__ = (UniqueConstraint('envid', 'id'),)

    @classmethod
    def get(cls, envid, tid, **kwargs):
        keys = {'envid':envid, 'id':tid}
        return cls.get_unique_by_keys(keys, **kwargs)

    @classmethod
    def sync(cls, agent):
        stmt = 'SELECT * FROM datasources'

        data = agent.odbc.execute(stmt)
        if 'error' in data:
            return data
        if '' not in data:
            data['error'] = "Missing '' key in query response."
            return data

        ids = []

        envid = agent.server.environment.envid

        session = meta.Session()
        for odbcdata in ODBC.load(data):
            tid = odbcdata.data['id']
            entry = DataSource.get(envid, tid, default=None)
            if not entry:
                entry = DataSource(envid=envid)
                session.add(entry)
            odbcdata.copyto(entry)
            ids.append(entry.dsid)

        session.query(DataSource).\
            filter(not_(DataSource.dsid.in_(ids))).\
            delete(synchronize_session='fetch')

        session.commit()

        d = {u'status': 'OK', u'count': len(data[''])}
        return d

