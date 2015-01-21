from abc import ABCMeta, abstractmethod, abstractproperty
from webob import exc

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from controller.cloud import CloudEntry
from controller.general import SystemConfig
from controller.files import FileManager


class CloudApplication(object):

    __metaclass__ = ABCMeta

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
        cloudid = req.system.getint(self.KEY, cleanup=True, default=None)
        if cloudid is None:
            return None
        return cloudid

    def get_req(self, req):
        cloudid = self._get_cloudid(req)
        if cloudid is None:
            return None
        entry = CloudEntry.get_by_envid_cloudid(req.envid, cloudid)
        print "entry:", self._todict(entry)
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
        data = entry.todict(pretty=True)
        data['secret-key'] = data['secret']
        del data['secret']
        data['url'] = self.bucket_to_url(data['bucket'])
        return data

    def cloud_save(self, req):
        # pylint: disable=invalid-name
        bucket = self.url_to_bucket(req.POST['url'])
        if not bucket:
            raise exc.HTTPBadRequest()

        session = meta.Session()

        entry = self._get_by_type(req.envid)
        # The name and the bucket are currently the same.
        entry.name = bucket
        entry.bucket = bucket
        entry.access_key = req.POST['access-key']
        entry.secret = req.POST['secret-key']
        session.commit()

        req.system.save(self.KEY, entry.cloudid)
        session.commit()

        req.system.save(SystemConfig.BACKUP_DEST_ID, entry.cloudid)
        req.system.save(SystemConfig.BACKUP_DEST_TYPE,
                                            FileManager.STORAGE_TYPE_CLOUD)

        return self._todict(entry)

    def cloud_remove(self, req):
        # pylint: disable=invalid-name
        # 'action' is just sanity check, its not used.
        req.system.delete(self.KEY)
        meta.Session().commit()
        return {}
