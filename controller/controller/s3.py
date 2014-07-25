import boto

from sqlalchemy import Column, BigInteger, String
from akiri.framework.ext.sqlalchemy import meta
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import ForeignKey

from mixin import OnlineMixin

# FIXME: This policy is *way* too permissive.
POLICY = '{"Statement":[{"Effect":"Allow","Action": "s3:*","Resource":"*"}]}'

class S3(meta.Base, OnlineMixin):
    __tablename__ = 's3'

    s3id = Column(BigInteger, unique=True, nullable=False, \
                      autoincrement=True, primary_key=True)
    envid = Column(BigInteger, ForeignKey("environment.envid"))
    name = Column(String, unique=True, index=True)
    bucket = Column(String, unique=True)
    access_key = Column(String)
    secret = Column(String)
    region = Column(String)

    def __init__(self, envid):
        self.envid = envid

    def get_token(self, resource):
        c = boto.connect_sts(aws_access_key_id=str(self.access_key),
                             aws_secret_access_key=str(self.secret))
        return c.get_federation_token(resource, policy=POLICY)

    def get_by_name(self, name):
        try:
            entry = meta.Session.query(S3).\
                filter(S3.envid == self.envid).\
                filter(S3.name == name).one()
            return entry
        except NoResultFound, e:
            return None

    def get_by_s3id(self, s3id):
        try:
            entry = meta.Session.query(S3).\
                filter(S3.envid == self.envid).\
                filter(S3.s3id == s3id).one()
            return entry
        except NoResultFound, e:
            return None

    @classmethod
    def get_by_s3id_envid(cls, s3id, envid):
        try:
            entry = meta.Session.query(S3).\
                filter(S3.envid == envid).\
                filter(S3.s3id == s3id).one()
            return entry
        except NoResultFound, e:
            return None

    @classmethod
    def get_by_envid_name(cls, envid, name):
        try:
            entry = meta.Session.query(S3).\
                filter(S3.envid == envid).\
                filter(S3.name == name).one()
            return entry
        except NoResultFound, e:
            return None

    @classmethod
    def insert_or_update(cls, envid, name, key, value):
        try:
            entry = meta.Session.query(S3).\
                filter(S3.envid == envid).\
                filter(S3.name == name).one()
        except NoResultFound, e:
            entry = None

        if entry is None:
            entry = S3(envid = envid)
            entry.name = name
            meta.Session.add(entry)

        if key == 'access-key-id':
            entry.access_key = value
        elif key == 'access-key-secret':
            entry.secret = value
        elif key == 'bucket-name':
             entry.bucket = value

        meta.Session.commit()

