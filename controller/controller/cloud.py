from sqlalchemy import Column, BigInteger, String
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import ForeignKey, UniqueConstraint

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

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

    CLOUD_TYPE_S3 = 's3'
    CLOUD_TYPE_GCS = 'gcs'

    # FIXME: use get_unique_by_keys()
    def get_by_name(self, name, cloud_type):
        try:
            entry = meta.Session.query(CloudEntry).\
                filter(CloudEntry.envid == self.envid).\
                filter(CloudEntry.cloud_type == cloud_type).\
                filter(CloudEntry.name == name).one()
            return entry
        except NoResultFound:
            return None

    # FIXME: use get_unique_by_keys()
    def get_by_cloudid(self, cloudid):
        try:
            entry = meta.Session.query(CloudEntry).\
                filter(CloudEntry.envid == self.envid).\
                filter(CloudEntry.cloudid == cloudid).one()
            return entry
        except NoResultFound:
            return None

    @classmethod
    def get_by_cloudid_envid(cls, cloudid, envid):
        # FIXME: use get_unique_by_keys()
        try:
            entry = meta.Session.query(CloudEntry).\
                filter(CloudEntry.envid == envid).\
                filter(CloudEntry.cloudid == cloudid).one()
            return entry
        except NoResultFound:
            return None

    @classmethod
    def get_by_envid_name(cls, envid, name, cloud_type):
        # FIXME: use get_unique_by_keys()
        try:
            entry = meta.Session.query(CloudEntry).\
                filter(CloudEntry.envid == envid).\
                filter(CloudEntry.cloud_type == cloud_type).\
                filter(CloudEntry.name == name).one()
            return entry
        except NoResultFound:
            return None

    @classmethod
    def get_clouds_by_envid(cls, envid):
        # FIXME: use get_all_by_keys()
        return meta.Session.query(CloudEntry).\
            filter_by(envid=envid).\
            order_by('cloud.name').\
            all()

    @classmethod
    def text(cls, value):
        if value == CloudManager.CLOUD_TYPE_S3:
            return 'Amazon S3 Storage'
        if value == CloudManager.CLOUD_TYPE_GCS:
            return 'Google Cloud Storage'
        raise KeyError(value)
