from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy import Integer, BigInteger, SmallInteger
from sqlalchemy import not_
from sqlalchemy.orm.exc import NoResultFound

from akiri.framework.ext.sqlalchemy import meta

class Project(meta.Base):
    __tablename__ = 'projects'

    projectid = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    state = Column(String(32))
    description = Column(String)
    site_id = Column(Integer, nullable=False)
    special = Column(Integer)

    @classmethod
    def get(cls, projectid):
        try:
            entry = meta.Session.query(Project).\
                filter(Project.projectid == projectid).one()
        except NoResultFound, e:
            entry = None
        return entry

    @classmethod
    def all(cls):
        return meta.Session.query(Project).order_by(Project.name).all()

    @classmethod
    def sync(cls, agent):
        stmt = \
            'SELECT id, name, owner_id, created_at, updated_at, ' +\
            'state, description, site_id, special ' +\
            'FROM projects'

        data = agent.odbc.execute(stmt)
        if 'error' in data:
            return data
        if '' not in data:
            data['error'] = "Missing '' key in query response."

        ids = []

        session = meta.Session()
        for row in data['']:
            entry = Project.get(row[0])
            if not entry:
                entry = Project(projectid=row[0])
                session.add(entry)
            entry.name = row[1]
            entry.owner_id = row[2]
            entry.created_at = row[3]
            entry.updated_at = row[4]
            entry.state = row[5]
            entry.description = row[6]
            entry.site_id = row[7]
            entry.special = row[8]
            ids.append(entry.projectid)

        session.query(Project).\
            filter(not_(Project.projectid.in_(ids))).\
            delete(synchronize_session='fetch')
    
        session.commit()

        d = {u'status': 'OK', u'count': len(data[''])}
        return d
