import os
import ntpath

import boto
from boto.s3 import connection

from abc import ABCMeta, abstractmethod

from sqlalchemy import Column, BigInteger, DateTime, String, func
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import ForeignKey, UniqueConstraint

import akiri.framework.sqlalchemy as meta

from mixin import BaseMixin, BaseDictMixin, OnlineMixin
from manager import Manager
from passwd import aes_decrypt

# FIXME: This policy is *way* too permissive.
S3_POLICY = '{"Statement":[{"Effect":"Allow","Action": "s3:*","Resource":"*"}]}'
S3_ID = 's3-id'
GCS_ID = 'gcs-id'

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

    __table_args__ = (UniqueConstraint('envid', 'name'),)

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
    def get_by_envid_name(cls, envid, name, cloud_type):
        filters = {'envid':envid, 'cloud_type':cloud_type, 'name':name}
        return cls.get_unique_by_keys(filters, default=None)

    @classmethod
    def get_all_by_envid(cls, envid):
        filters = {'envid':envid}
        return cls.get_all_by_keys(filters, order_by='name')

class CloudManager(Manager):

    CLOUD_TYPE_S3 = 's3'
    CLOUD_TYPE_GCS = 'gcs'

    def __init__(self, server):
        super(CloudManager, self).__init__(server)
        # pylint: disable=invalid-name
        self.s3 = S3(server)
        self.gcs = GCS(server)
        self.server = server

    def get_by_name(self, name, cloud_type):
        return CloudEntry.get_by_envid_name(self.envid, name, cloud_type)

    def get_clouds(self):
        return CloudEntry.get_all_by_envid(self.envid)

    def get_cloud_entry(self, cloud_type_id):
        """Return the current entry of cloud_type_id (S3_ID or GCS_ID),
           or None if there isn't one."""
        cloudid = self.server.system.getint(cloud_type_id, default=0)
        if not cloudid:
            return None

        return self.get_by_cloudid(cloudid)

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
    def text(cls, value):
        if value == CloudManager.CLOUD_TYPE_S3:
            return 'Amazon S3 Storage'
        if value == CloudManager.CLOUD_TYPE_GCS:
            return 'Google Cloud Storage'
        raise KeyError(value)


def move_bucket_subdirs_to_path(in_bucket, in_path):
    """ Given:
      in_bucket: palette-storage/subdir/dir2
      in_path:   filename
      return:
        bucket:    palette-storage
        path:      subdir/dir2/filename
    """

    if in_bucket.find('/') != -1:
        bucket, rest = in_bucket.split('/', 1)
        path = os.path.join(rest, in_path)
    elif in_bucket.find('\\') != -1:
        bucket, rest = in_bucket.split('\\', 1)
        path = ntpath.join(rest, in_path)
    else:
        bucket = in_bucket
        path = in_path
    return (bucket, path)

# Abstract base class for S3 and GCS.
class CloudInstance(object):
    __metaclass__ = ABCMeta

    def __init__(self, server):
        self.server = server
        self.envid = self.server.environment.envid

    @abstractmethod
    def send_cmd(self, agent, action, cloud_entry, path, bucket_subdir=None,
                                                                    pwd=None):
        # pylint: disable=too-many-arguments
        pass

    @abstractmethod
    def delete_file(self, entry, path):
        pass

    # pylint: disable=too-many-arguments
    def get(self, agent, cloud_entry, path, bucket_subdir=None, pwd=None):
        return self.send_cmd(agent, 'GET', cloud_entry, path,
                                        bucket_subdir=bucket_subdir, pwd=pwd)

    # pylint: disable=too-many-arguments
    def put(self, agent, cloud_entry, path, bucket_subdir=None, pwd=None):
        return self.send_cmd(agent, 'PUT', cloud_entry, path,
                                        bucket_subdir=bucket_subdir, pwd=pwd)

# Handle S3 specifics
class S3(CloudInstance):

    def send_cmd(self, agent, action, cloud_entry, path, bucket_subdir=None,
                                                                    pwd=None):
        # pylint: disable=too-many-arguments
        # fixme: sanity check on data-dir on the primary?
        # fixme: create the path first

        # pylint: disable=pointless-string-statement
        """
        # fixme: Not all users have authorization to do this.
        resource = os.path.basename(filename)
        try:
            token = cloud_entry.get_token(resource)
        except (AWSConnectionError, BotoClientError, BotoServerError) as e:
            return self.error("s3: %s" % str(e))

        # fixme: this method doesn't work
        env = {u'ACCESS_KEY': token.credentials.access_key,
               u'SECRET_KEY': token.credentials.secret_key,
               u'SESSION': token.credentials.session_token,
               u'REGION_ENDPOINT': cloud_entry.region,
               u'PWD': pwd}
        """

        secret = aes_decrypt(cloud_entry.secret)
        env = {u'ACCESS_KEY': cloud_entry.access_key,
               u'SECRET_KEY': secret}

        if pwd:
            env['PWD'] = pwd
        elif agent.data_dir:
            env['PWD'] = agent.data_dir

        if action == 'GET':
            arg1 = cloud_entry.bucket

            if bucket_subdir:
                arg2 = os.path.join(bucket_subdir, path)
            else:
                arg2 = path

        elif action == 'PUT':
            if bucket_subdir:
                arg1 = os.path.join(cloud_entry.bucket, bucket_subdir)
            else:
                arg1 = cloud_entry.bucket
            arg2 = path
        else:
            raise IOError("S3 send_cmd bad action: " + action)

        s3_command = 'ps3 %s %s "%s"' % (action, arg1, arg2)

        self.server.log.debug("s3_command: '%s', pwd: '%s', path: '%s'",
                              s3_command, pwd, path)

        # Send the s3 command to the agent
        return self.server.cli_cmd(s3_command, agent, env=env, timeout=60*60*2)

    def delete_file(self, entry, path):
        # Move any bucket subdirectories to the filename
        bucket_name, filename = move_bucket_subdirs_to_path(entry.bucket, path)

        # fixme: use temporary token if configured for it
        secret = aes_decrypt(entry.secret)
        conn = connection.S3Connection(entry.access_key, secret)

        bucket = connection.Bucket(conn, bucket_name)

        s3key = connection.Key(bucket)
        s3key.key = filename
        try:
            bucket.delete_key(s3key)
        except boto.exception.BotoServerError as ex:
            raise IOError(
                    ("Failed to delete '%s' from S3 Cloud Storage " + \
                    "bucket '%s'. %s: %s") % \
                    (filename, bucket_name, ex.reason, ex.message))
        return {'status': 'OK'}


class GCS(CloudInstance):

    def send_cmd(self, agent, action, cloud_entry, path, bucket_subdir=None,
                                                                    pwd=None):
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-arguments

        # fixme: sanity check on data-dir on the primary?

        # FIXME: We don't really want to send our real keys and
        #        secrets to the agents, but while boto.connect_gs
        #        can replace boto.connect_s3, there is no GCS
        #        equivalent for boto.connect_sts, so we may need
        #        to move away from boto to get GCS temporary tokens.
        secret = aes_decrypt(cloud_entry.secret)
        env = {u'ACCESS_KEY': cloud_entry.access_key,
               u'SECRET_KEY': secret}

        if pwd:
            env['PWD'] = pwd
        elif agent.data_dir:
            env['PWD'] = agent.data_dir

        if action == 'GET':
            arg1 = cloud_entry.bucket

            if bucket_subdir:
                arg2 = os.path.join(bucket_subdir, path)
            else:
                arg2 = path
        elif action == 'PUT':
            if bucket_subdir:
                arg1 = os.path.join(cloud_entry.bucket, bucket_subdir)
            else:
                arg1 = cloud_entry.bucket
            arg2 = path
        else:
            raise IOError("GCS send_cmd bad action: " + action)

        gcs_command = 'pgcs %s %s "%s"' % (action, arg1, arg2)

        # Send the gcs command to the agent
        body = self.server.cli_cmd(gcs_command, agent, env=env, timeout=60*60*2)
        return body

    def delete_file(self, entry, path):
        # Move any bucket subdirectories to the filename
        bucket_name, filename = move_bucket_subdirs_to_path(entry.bucket, path)

        secret = aes_decrypt(entry.secret)
        conn = boto.connect_gs(entry.access_key, secret)
        try:
            bucket = conn.get_bucket(bucket_name)
        except boto.exception.GSResponseError as ex:
            # Can happen when the secret is very bad.
            raise IOError(
                    ("Failed to delete '%s' on Google Cloud Storage " + \
                    "bucket '%s': %s") % \
                    (filename, bucket_name, str(ex)))

        # boto uses s3 keys for GCS ??
        s3key = boto.s3.key.Key(bucket)
        s3key.key = filename

        try:
            s3key.delete()
        except boto.exception.BotoServerError as ex:
            if ex.status != 404:
                raise IOError(
                    ("Failed to delete '%s' from Google Cloud Storage " + \
                    "bucket '%s': %s") % \
                    (filename, bucket_name, str(ex)))
        return {'status': 'OK'}
