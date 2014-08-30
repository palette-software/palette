import boto

from sqlalchemy import Column, BigInteger, String
from akiri.framework.ext.sqlalchemy import meta
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import ForeignKey, UniqueConstraint

from mixin import BaseDictMixin, OnlineMixin
from manager import Manager

# FIXME: This policy is *way* too permissive.
S3_POLICY = '{"Statement":[{"Effect":"Allow","Action": "s3:*","Resource":"*"}]}'

class CloudEntry(meta.Base, BaseDictMixin, OnlineMixin):
    __tablename__ = 'cloud'

    cloudid = Column(BigInteger, unique=True, nullable=False, \
                      autoincrement=True, primary_key=True)
    envid = Column(BigInteger, ForeignKey("environment.envid"))
    cloud_type = Column(String)  # s3 or gcs
    name = Column(String, index=True)
    bucket = Column(String, unique=True)
    access_key = Column(String)
    secret = Column(String)
    region = Column(String)

    UniqueConstraint('envid', 'name')

class CloudManager(Manager):

    CLOUD_TYPE_S3='s3'
    CLOUD_TYPE_GCS='gcs'

    def get_by_name(self, name, cloud_type):
        try:
            entry = meta.Session.query(CloudEntry).\
                filter(CloudEntry.envid == self.envid).\
                filter(CloudEntry.cloud_type == cloud_type).one().\
                filter(CloudEntry.name == name).one()
            return entry
        except NoResultFound, e:
            return None

    def get_by_cloudid(self, cloudid):
        try:
            entry = meta.Session.query(CloudEntry).\
                filter(CloudEntry.envid == self.envid).\
                filter(CloudEntry.cloudid == cloudid).one()
            return entry
        except NoResultFound, e:
            return None

    def get_s3_token(self, resource):
        c = boto.connect_sts(aws_access_key_id=str(self.access_key),
                             aws_secret_access_key=str(self.secret))
        return c.get_federation_token(resource, policy=S3_POLICY)

    @classmethod
    def get_by_cloudid_envid(cls, cloudid, envid):
        try:
            entry = meta.Session.query(CloudEntry).\
                filter(CloudEntry.envid == envid).\
                filter(CloudEntry.cloudid == cloudid).one()
            return entry
        except NoResultFound, e:
            return None

    @classmethod
    def get_by_envid_name(cls, envid, name, cloud_type):
        try:
            entry = meta.Session.query(CloudEntry).\
                filter(CloudEntry.envid == envid).\
                filter(CloudEntry.cloud_type == cloud_type).\
                filter(CloudEntry.name == name).one()
            return entry
        except NoResultFound, e:
            return None

    @classmethod
    def get_clouds_by_envid(cls, envid):
        return meta.Session.query(CloudEntry).\
            filter_by(envid = envid).\
            order_by('cloud.name').\
            all()
