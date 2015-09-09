from abc import ABCMeta, abstractmethod, abstractproperty
from webob import exc

import akiri.framework.sqlalchemy as meta

from controller.cloud import CloudEntry
from controller.files import FileManager
from controller.passwd import aes_encrypt
from controller.system import SystemKeys

class CloudApplication(object):

    __metaclass__ = ABCMeta

    @abstractproperty
    def NAME(self):
        # pylint: disable=invalid-name
        pass

    @abstractproperty
    def KEY(self):
        # pylint: disable=invalid-name
        pass

    @abstractproperty
    def TYPE(self):
        # pylint: disable=invalid-name
        pass

    @abstractmethod
    def url_to_bucket(self, url):
        pass

    @abstractmethod
    def bucket_to_url(self, bucket):
        pass

    def _get_cloudid(self, req):
        cloudid = req.system[self.KEY]
        if cloudid is None:
            return None
        return cloudid

    def get_req(self, req):
        cloudid = self._get_cloudid(req)
        if cloudid is None:
            return {}
        entry = CloudEntry.get_by_envid_cloudid(req.envid, cloudid)
        return self._todict(entry)

    # Not used yet.  Will be used when multiple cloud names for
    # one cloud type are supported.
    def _get_by_name(self, envid, name):
        entry = CloudEntry.get_by_envid_name(envid, name, self.TYPE)
        if entry is None:
            entry = CloudEntry(envid=envid, cloud_type=self.TYPE)
            # The name and the bucket are currently the same.
            entry.name = name
            entry.bucket = name
            meta.Session.add(entry)
        return entry

    def _get_by_type(self, envid):
        entry = CloudEntry.get_by_envid_type(envid, self.TYPE)
        if entry is None:
            entry = CloudEntry(envid=envid, cloud_type=self.TYPE)
            meta.Session.add(entry)
        return entry

    def _todict(self, entry):
        data = {}
        data[self.NAME + '-access-key'] = entry.access_key
        data[self.NAME + '-secret-key'] = entry.secret
        data[self.NAME + '-url'] = self.bucket_to_url(entry.bucket)
        return data

    def cloud_save(self, req):
        # pylint: disable=invalid-name
        bucket = self.url_to_bucket(req.POST['url'])
        if not bucket:
            raise exc.HTTPBadRequest()

        entry = self._get_by_type(req.envid)
        # The name and the bucket are currently the same.
        entry.name = bucket
        entry.bucket = bucket
        entry.access_key = req.POST['access-key']
        entry.secret = aes_encrypt(req.POST['secret-key'])

        req.system[self.KEY] = entry.cloudid

        backup_dest_type = FileManager.STORAGE_TYPE_CLOUD
        req.system[SystemKeys.BACKUP_DEST_TYPE] = backup_dest_type
        req.system[SystemKeys.BACKUP_DEST_ID] = entry.cloudid

        meta.commit()
        return self._todict(entry)

    def cloud_remove(self, req):
        # 'action' is just sanity check, its not used.
        del req.system[self.KEY]
        meta.commit()
        return {}
