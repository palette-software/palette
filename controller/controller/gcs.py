from sqlalchemy import Column, BigInteger, String
from akiri.framework.ext.sqlalchemy import meta
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import ForeignKey

class GCS(meta.Base):
    __tablename__ = 'gcs'

    gcsid = Column(BigInteger, unique=True, nullable=False, \
                      autoincrement=True, primary_key=True)
    envid = Column(BigInteger, ForeignKey("environment.envid"))
    name = Column(String, unique=True, index=True)
    bucket = Column(String, unique=True)
    access_key = Column(String)
    secret = Column(String)

    def __init__(self, envid):
        self.envid = envid

    def get_by_name(self, name):
        try:
            entry = meta.Session.query(GCS).\
                filter(GCS.envid == self.envid).\
                filter(GCS.name == name).one()
            return entry
        except NoResultFound, e:
            return None

    def get_by_gcsid(self, gcsid):
        try:
            entry = meta.Session.query(GCS).\
                filter(GCS.envid == self.envid).\
                filter(GCS.gcsid == gcsid).one()
            return entry
        except NoResultFound, e:
            return None

    @classmethod
    def get_by_gcsid_envid(cls, gcsid, envid):
        try:
            entry = meta.Session.query(GCS).\
                filter(GCS.envid == envid).\
                filter(GCS.gcsid == gcsid).one()
            return entry
        except NoResultFound, e:
            return None


    def get_all(self):
        return meta.Session.query(GCS).\
            filter(GCS.envid == self.envid).\
            all()
