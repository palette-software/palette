import logging
import os
import ntpath

from urlparse import urlsplit

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
from .system import SystemKeys
from .util import failed

logger = logging.getLogger()

CLOUD_TYPE_S3 = 's3'
CLOUD_TYPE_GCS = 'gcs'

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

    __table_args__ = (UniqueConstraint('envid', 'name'),)

    @property
    def secret_key(self):
        return aes_decrypt(self.secret)

    @property
    def scheme(self):
        if self.cloud_type == CLOUD_TYPE_S3:
            return 's3'
        elif self.cloud_type == CLOUD_TYPE_GCS:
            return 'gs'
        # FIXME: assert and/or enum
        return None

    @classmethod
    def get_by_envid_cloudid(cls, envid, cloudid):
        """ envid is a sanity check (not technically needed) """
        filters = {'envid':envid, 'cloudid':cloudid}
        return cls.get_unique_by_keys(filters, default=None)

    @classmethod
    def get_by_id(cls, cloudid):
        filters = {'cloudid':cloudid}
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


class CloudInfo(object):
    """ Non-sqlalchemy class representing a file in the cloud.
    This class should have all information necessary to download the file.
    """

    def __init__(self, cloud_type, path):
        if cloud_type not in (CLOUD_TYPE_S3, CLOUD_TYPE_GCS):
            raise ValueError("Invalid cloud type: " + cloud_type)
        self.cloud_type = cloud_type
        self.path = path
        self.bucket = None
        self.access_key = None
        self.secret_key = None

    @classmethod
    def from_url(cls, url):
        """ Create an instance using a url string or ParseResult. """
        if isinstance(url, basestring):
            url = urlsplit(url)
        if not url.path:
            raise ValueError("No path specified in URL.")

        # urlsplit lower-cases the scheme.
        if url.scheme == 's3':
            cloud_info = CloudInfo(CLOUD_TYPE_S3, url.path)
        elif url.scheme == 'gs':
            cloud_info = CloudInfo(CLOUD_TYPE_GCS, url.path)
        else:
            raise ValueError("Invalid URL '" + url.scheme + "', " +
                             "the scheme must be 's3' or 'gcs'")
        if url.hostname:
            cloud_info.bucket = url.hostname
        if url.username:
            if not url.password:
                raise ValueError("The secret_key is required " +
                                 "when the access_key is specified")
            cloud_info.access_key = url.username
        if url.password:
            if not url.username:
                raise ValueError("The access_key is required " +
                                 "when the secret_key is specified")
            cloud_info.secret_key = url.password
        return cloud_info

    @classmethod
    def from_cloud_entry(cls, entry, path):
        """ Build a instance from a path and a CloudEntry instance. """
        cloud_info = CloudInfo(entry.cloud_type, path)
        cloud_info.bucket = entry.bucket
        cloud_info.access_key = entry.access_key
        cloud_info.secret_key = entry.secret_key
        return cloud_info


class CloudManager(Manager):

    CLOUD_TYPE_S3 = CLOUD_TYPE_S3
    CLOUD_TYPE_GCS = CLOUD_TYPE_GCS

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
        cloudid = self.system[cloud_type_id]
        if not cloudid:
            return None

        return self.get_by_cloudid(cloudid)

    def delete_cloud_file_by_file_entry(self, file_entry):
        """Note: Does not remove the entry from the files table.
           If that is needed, that must be done by the caller."""
        cloud_entry = self.get_by_cloudid(file_entry.storageid)
        if not cloud_entry:
            raise IOError("No such cloudid: %d for file %s" % \
                          (file_entry.cloudid, file_entry.name))

        if cloud_entry.cloud_type == CloudManager.CLOUD_TYPE_S3:
            self.s3.delete_file(cloud_entry, file_entry.name)
        elif cloud_entry.cloud_type == CloudManager.CLOUD_TYPE_GCS:
            self.gcs.delete_file(cloud_entry, file_entry.name)
        else:
            msg = "delete_cloud_file: Unknown cloud_type %s for file: %s" % \
                  (cloud_entry.cloud_type, file_entry.name)
            logging.error(msg)
            raise IOError(msg)

    def download(self, agent, url, pwd=None):
        """
        Download the file pointed to by 'url' into the agent data-dir and
        return the body of the cli_cmd

        raises: ValueError, IOError (?)
        """
        cloud_info = CloudInfo.from_url(url)

        if cloud_info.cloud_type == CLOUD_TYPE_S3:
            send_get = self.s3.send_get
            cloud_type_id = SystemKeys.S3_ID
        elif cloud_info.cloud_type == CLOUD_TYPE_GCS:
            send_get = self.gcs.send_get
            cloud_type_id = SystemKeys.GCS_ID
        else:
            assert False

        # Now try to fill in the cloud_info with any credentials.

        # The url 'hostname' is the bucket which is also the entry 'name'.
        if cloud_info.bucket:
            cloud_entry = self.get_by_name(cloud_info.bucket,
                                           cloud_info.cloud_type)
        else:
            cloud_entry = self.get_cloud_entry(cloud_type_id)

        if cloud_entry:
            if not cloud_info.bucket:
                cloud_info.bucket = cloud_entry.bucket
            if not cloud_info.access_key:
                cloud_info.access_key = cloud_entry.access_key
                cloud_info.secret_key = cloud_entry.secret_key

        if not cloud_info.bucket:
            raise ValueError("The bucket name is required.")

        return send_get(agent, cloud_info, pwd=pwd)

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


def _cloud_command_environment(agent, cloud_info, pwd=None):
    """ Build the environment dict sent to send to ps3/pgcs
          keys: ACCESS_KEY, SECRET_KEY and PWD
    """
    env = {}
    if cloud_info.access_key:
        env['ACCESS_KEY'] = cloud_info.access_key
    if cloud_info.secret_key:
        env['SECRET_KEY'] = cloud_info.secret_key

    if not pwd:
        if agent.data_dir:
            pwd = agent.data_dir
        elif agent.install_dir:
            pwd = agent.install_dir
    if pwd:
        env[u'PWD'] = pwd
    if not env:
        return None
    return env


# Abstract base class for S3 and GCS.
class CloudInstance(object):
    __metaclass__ = ABCMeta

    EXE = None

    def __init__(self, server):
        self.server = server
        self.envid = self.server.environment.envid

    @abstractmethod
    def delete_file(self, entry, path):
        pass

    # NOTE: no bucket_subdir, include it as part of the path.
    def get(self, agent, cloud_entry, path, pwd=None):
        cloud_info = CloudInfo.from_cloud_entry(cloud_entry, path)
        return self.send_get(agent, cloud_info, pwd=pwd)

    def put(self, agent, cloud_entry, filepath, bucket_subdir=None, pwd=None):
        # pylint: disable=too-many-arguments
        cloud_path = agent.path.basename(filepath)
        if bucket_subdir:
            cloud_path = os.path.join(bucket_subdir, cloud_path)
        cloud_info = CloudInfo.from_cloud_entry(cloud_entry, cloud_path)
        return self.send_put(agent, cloud_info, filepath, pwd=pwd)

    def send_put(self, agent, cloud_info, filepath, pwd=None):
        """ Perform a PUT of the file specified by cloud_info """
        # fixme: sanity check on data-dir on the primary?
        # fixme: create the path first

        env = _cloud_command_environment(agent, cloud_info, pwd)

        bucket_subdir = os.path.dirname(cloud_info.path)
        arg1 = os.path.join(cloud_info.bucket, bucket_subdir)
        arg2 = filepath

        assert not self.EXE is None
        cmd = '%s PUT %s "%s"' % (self.EXE, arg1, arg2)

        logger.debug("cmd: '%s', pwd: '%s', path: '%s'",
                     cmd, str(pwd), filepath)

        # Send the command to the agent
        return self.server.cli_cmd(cmd, agent, env=env, timeout=60*60*2)

    def send_get(self, agent, cloud_info, pwd=None):
        """ Perform a GET on the file specified by cloud_info """
        # fixme: sanity check on data-dir on the primary?
        # fixme: create the path first

        env = _cloud_command_environment(agent, cloud_info, pwd)
        arg1 = cloud_info.bucket
        arg2 = cloud_info.path

        if arg2.startswith('/'):
            arg2 = arg2[1:]

        assert not self.EXE is None
        cmd = '%s GET %s "%s"' % (self.EXE, arg1, arg2)

        logger.debug("cmd: '%s', pwd: '%s'", cmd, str(pwd))

        # Send the command to the agent
        body = self.server.cli_cmd(cmd, agent, env=env, timeout=60*60*2)
        if failed(body):
            return body

        if not 'path' in body:
            path = os.path.basename(cloud_info.path)
            if env and 'PWD' in env:
                body['path'] = agent.path.join(env['PWD'], path)
            else:
                body['path'] = path
        return body


# Handle S3 specifics
class S3(CloudInstance):
    """
    For now S3 send_cmd is generic, but eventually it will evolve to use
    temporary tokens:

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

    EXE = 'ps3'

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

    EXE = 'pgcs'

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
