from sqlalchemy import Column, BigInteger, DateTime, String, func
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import ForeignKey, UniqueConstraint

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from mixin import BaseMixin, BaseDictMixin, OnlineMixin
from manager import Manager

# FIXME: This policy is *way* too permissive.
S3_POLICY = '{"Statement":[{"Effect":"Allow","Action": "s3:*","Resource":"*"}]}'

class CloudEntry(meta.Base, BaseMixin, BaseDictMixin, OnlineMixin):
    __tablename__ = 'cloud'

    cloudid = Column(BigInteger, unique=True, nullable=False, \
                      autoincrement=True, primary_key=True)
    envid = Column(BigInteger, ForeignKey("environment.envid"))
    cloud_type = Column(String)  # s3 or gcs
    name = Column(String, index=True)
    bucket = Column(String, nullable=False)
    access_key = Column(String, nullable=False)
    secret = Column(String, nullable=False)
    region = Column(String)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(),
                               server_onupdate=func.current_timestamp())

    __table_args__ = (UniqueConstraint('envid', 'name'),
                      UniqueConstraint('envid', 'bucket'))

    @classmethod
    def get_by_envid_cloudid(cls, envid, cloudid):
        filters = {'envid':envid, 'cloudid':cloudid}
        return cls.get_unique_by_keys(filters, default=None)

    @classmethod
    def get_by_envid_type(cls, envid, cloud_type):
        session = meta.Session()
        filters = {'envid':envid, 'cloud_type':cloud_type}

        # pylint: disable=maybe-no-member
        subquery = session.query(func.max(cls.modification_time))
        subquery = cls.apply_filters(subquery, filters).subquery()

        query = session.query(cls).filter(cls.modification_time.in_(subquery))
        try:
            # There is a *theoretical* possibility that multiple records
            # could have the same timestamp so just take the first.
            return query.first()
        except NoResultFound:
            return None

    @classmethod
    def get_by_envid_bucket(cls, envid, bucket, cloud_type):
        filters = {'envid':envid, 'cloud_type':cloud_type, 'bucket':bucket}
        return cls.get_unique_by_keys(filters, default=None)

    @classmethod
    def get_by_envid_name(cls, envid, name, cloud_type):
        filters = {'envid':envid, 'cloud_type':cloud_type, 'name':name}
        return cls.get_unique_by_keys(filters, default=None)


class CloudManager(Manager):

    CLOUD_TYPE_S3 = 's3'
    CLOUD_TYPE_GCS = 'gcs'

    def get_by_name(self, name, cloud_type):
        return CloudEntry.get_by_envid_name(self.envid, name, cloud_type)

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
