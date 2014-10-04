from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy import not_, UniqueConstraint
from sqlalchemy.schema import ForeignKey

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from mixin import BaseMixin

class Project(meta.Base, BaseMixin):
    #pylint: disable=too-many-instance-attributes
    __tablename__ = 'projects'

    # FIXME: BigInteger
    projectid = Column(Integer, primary_key=True)
    envid = Column(Integer, ForeignKey("environment.envid"), nullable=False)
    name = Column(String, nullable=False)
    owner_id = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    state = Column(String(32))
    description = Column(String)
    site_id = Column(Integer, nullable=False)
    special = Column(Integer)

    __table_args__ = (UniqueConstraint('envid', 'projectid'),)

    @classmethod
    def get(cls, envid, projectid, **kwargs):
        keys = {'envid':envid, 'projectid':projectid}
        return cls.get_unique_by_keys(keys, **kwargs)

    @classmethod
    def get_name_by_id(cls, envid, projectid):
        entry = cls.get(envid, projectid, default=None)
        if entry is None:
            return None
        return entry.name

    @classmethod
    def all(cls, envid):
        return cls.get_all_by_keys({'envid':envid}, order_by='name')

    @classmethod
    def sync(cls, agent):
        envid = agent.server.environment.envid
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
            entry = Project.get(envid, row[0], default=None)
            if not entry:
                entry = Project(envid=envid, projectid=row[0])
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

        # FIXME: don't delete - mark inactive.
        session.query(Project).\
            filter(not_(Project.projectid.in_(ids))).\
            delete(synchronize_session='fetch')

        session.commit()

        d = {u'status': 'OK', u'count': len(data[''])}
        return d

    @classmethod
    def cache(cls, envid):
        return cls.cache_by_key(envid, key='projectid')
