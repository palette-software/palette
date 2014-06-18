import boto

from sqlalchemy import Column, BigInteger, String
from akiri.framework.ext.sqlalchemy import meta
from sqlalchemy.orm.exc import NoResultFound

# FIXME: This policy is *way* too permissive.
POLICY = '{"Statement":[{"Effect":"Allow","Action": "s3:*","Resource":"*"}]}'

class GCS(meta.Base):
    __tablename__ = 'gcs'

    gcsid = Column(BigInteger, unique=True, nullable=False, \
                      autoincrement=True, primary_key=True)
    name = Column(String, unique=True, index=True)
    bucket = Column(String, unique=True)
    access_key = Column(String)
    secret = Column(String)

    @classmethod
    def get_by_name(cls, name):
        try:
            entry = meta.Session.query(GCS).\
                filter(GCS.name == name).one()
            return entry
        except NoResultFound, e:
            return None