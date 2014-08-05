from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy import Integer, BigInteger, SmallInteger
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import not_

from akiri.framework.ext.sqlalchemy import meta

class DataConnection(meta.Base):
    __tablename__ = 'data_connections'

    dcid = Column(Integer, primary_key=True)
    server = Column(String)
    dbclass = Column(String)
    port = Column(Integer)
    username = Column(String)
    password = Column(Boolean)
    name = Column(String)
    dbname = Column(String)
    tablename = Column(String)
    owner_type = Column(String)
    owner_id = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    caption = Column(String)
    site_id = Column(Integer)
    keychain = Column(String)

    @classmethod
    def get(cls, dcid):
        try:
            entry = meta.Session.query(DataConnection).\
                filter(DataConnection.dcid == dcid).one()
        except NoResultFound, e:
            entry = None
        return entry

    @classmethod
    def sync(cls, agent):
        stmt = \
            'SELECT id, server, dbclass, port, username, password, ' +\
            'name, dbname, tablename, owner_type, owner_id, '+\
            'created_at, updated_at, caption, site_id, keychain ' +\
            'FROM data_connections'

        data = agent.odbc.execute(stmt)
        if 'error' in data:
            return data
        if '' not in data:
            data['error'] = "Missing '' key in query response."
            return data

        ids = []

        session = meta.Session()
        for row in data['']:
            entry = DataConnection.get(row[0])
            if not entry:
                entry = DataConnection(dcid=row[0])
            entry.server = row[1]
            entry.dbclass = row[2]
            entry.port = row[3]
            entry.username = row[4]
            entry.password = row[5]
            entry.name = row[6]
            entry.dbname = row[7]
            entry.tablename = row[8]
            entry.owner_type = row[9]
            entry.owner_id = row[10]
            entry.created_at = row[11]
            entry.updated_at = row[12]
            entry.caption = row[13]
            entry.site_id = row[14]
            entry.keychain = row[15]
            session.merge(entry)
            ids.append(entry.dcid)

        session.query(DataConnection).\
            filter(not_(DataConnection.dcid.in_(ids))).\
            delete(synchronize_session='fetch')

        session.commit()

        d = {u'status': 'OK', u'count': len(data[''])}
        return d
