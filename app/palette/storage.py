from webob import exc

from akiri.framework.ext.sqlalchemy import meta

from controller.profile import Role
from controller.agent import Agent
from controller.util import sizestr, str2bool
from controller.storage import StorageConfig

from controller.agentinfo import AgentVolumesEntry
from controller.s3 import S3
from controller.gcs import GCS

from page import PalettePage
from rest import PaletteRESTHandler, required_parameters, required_role

__all__ = ["StorageApplication"]

class StorageApplication(PaletteRESTHandler):
    NAME = 'storage'

    def __init__(self, global_conf):
        super(StorageApplication, self).__init__(global_conf)
        self.sc = StorageConfig(self.system)

    def build_item_for_volume(self, volume):
        fmt = "%s %s %s (%s Unused)"
        name = volume.name
        if volume.agent.iswin and len(name) == 1:
            name = name + ':'
        return fmt % (volume.agent.displayname, name,
                      sizestr(volume.size), sizestr(volume.available_space))

    def handle_get(self, req):
        sc = StorageConfig(self.system)
        data = {StorageConfig.STORAGE_ENCRYPT: sc.storage_encrypt,
                StorageConfig.WORKBOOKS_AS_TWB: sc.workbooks_as_twb}

        # populate the storage destination type
        dest = {'name': 'storage-destination'}
        options = []

        value = None
        destid = self.destid()
        for volume in AgentVolumesEntry.get_archives_by_envid(self.envid):
            item = self.build_item_for_volume(volume)
            ourid = '%s:%d' % (StorageConfig.VOL, volume.volid)
            options.append({'id': ourid, 'item':item})
            if destid == ourid:
                value = item

        for entry in S3.get_s3s_by_envid(self.envid):
            # fixme: If/when multiple s3 configs are available, distinguish
            # the s3 items from each other.
            item = sc.text(StorageConfig.S3)
            ourid = '%s:%d' % (StorageConfig.S3, entry.s3id)
            options.append({'id': ourid, 'item': item})

            if destid == ourid:
                value = item

        for entry in GCS.get_gcss_by_envid(self.envid):
            # fixme: If/when multiple gcs configs are available, distinguish
            # the gcs items from each other.
            item = sc.text(StorageConfig.GCS)
            ourid = '%s:%d' % (StorageConfig.GCS, entry.gcsid)
            options.append({'id': ourid, 'item': item})

            if destid == ourid:
                value = item

        if not options:
            # Placeholder until an agent connects.
            options.append({'id': StorageConfig.VOL,
                            'item': sc.text(StorageConfig.VOL)})

        if value is None:
            value = self.sc.text(destid)

        dest['value'] = value
        dest['options'] = options

        low = {'name': StorageConfig.WATERMARK_LOW,
               'value': str(sc.watermark_low)}
        options = []
        for x in [50, 55, 60, 65, 70]:
            options.append({'id':x, 'item': str(x)})
        low['options'] = options

        high = {'name': StorageConfig.WATERMARK_HIGH,
               'value': str(sc.watermark_high)}
        options = []
        for x in [75, 80, 85, 90, 95]:
            options.append({'id':x, 'item': str(x)})
        high['options'] = options

        auto = {'name': StorageConfig.BACKUP_AUTO_RETAIN_COUNT,
               'value': str(sc.backup_auto_retain_count)}
        options = []
        for x in [7,14,21,28]:
            options.append({'id':x, 'item': str(x)})
        auto['options'] = options

        options = []
        user = {'name': StorageConfig.BACKUP_USER_RETAIN_COUNT,
               'value': str(sc.backup_user_retain_count)}
        for x in range(1,11):
            options.append({'id':x, 'item': str(x)})
        user['options'] = options

        logs = {'name': StorageConfig.LOG_ARCHIVE_RETAIN_COUNT,
               'value': str(sc.log_archive_retain_count)}
        options = []
        for x in range(1,11):
            options.append({'id':x, 'item': str(x)})
        logs['options'] = options

        data['config'] = [dest, low, high, auto, user, logs]

        return data

    @required_parameters('value')
    def handle_yesno_POST(self, req, name):
        value = str2bool(req.POST['value'])
        s = value and 'yes' or 'no'
        self.system.save(name, s)
        return {'value':value}

    def handle_encryption(self, req):
        if req.method == 'GET':
            return {'value':self.sc.storage_encrypt}
        elif req.method == 'POST':
            return self.handle_yesno_POST(req, StorageConfig.STORAGE_ENCRYPT)
        else:
            raise exc.HTTPMethodNotAllowed()

    @required_parameters('id')
    def handle_dest_POST(self, req):
        value = req.POST['id']
        parts = value.split(':')
        if len(parts) != 2:
            print "Bad value:", value
            raise exc.HTTPBadRequest()

        (desttype, destid) = parts
        self.system.save(StorageConfig.BACKUP_DEST_ID, destid)
        self.system.save(StorageConfig.BACKUP_DEST_TYPE, desttype)
        return {'id':value}

    # return the id of the current selection (built from StorageConfig)
    def destid(self):
        dest_id = self.sc.backup_dest_id
        if dest_id == None:
            dest_id = 0

        value = self.sc.backup_dest_type
        return "%s:%d" % (self.sc.backup_dest_type, dest_id)

    def handle_dest(self, req):
        if req.method == 'GET':
            return {'id':self.destid()}
        elif req.method == 'POST':
            return self.handle_dest_POST(req)
        else:
            raise exc.HTTPMethodNotAllowed()

    @required_parameters('id')
    def handle_int_POST(self, req, name):
        value = req.POST['id']
        self.system.save(name, str(value))
        return {'id':value}

    def handle_low(self, req):
        if req.method == 'GET':
            return {'value':self.sc.watermark_low}
        elif req.method == 'POST':
            return self.handle_int_POST(req, StorageConfig.WATERMARK_LOW)
        else:
            raise exc.HTTPMethodNotAllowed()

    def handle_high(self, req):
        if req.method == 'GET':
            return {'value':self.sc.watermark_high}
        elif req.method == 'POST':
            return self.handle_int_POST(req, StorageConfig.WATERMARK_HIGH)
        else:
            raise exc.HTTPMethodNotAllowed()

    def handle_auto(self, req):
        if req.method == 'GET':
            return {'value':self.sc.backup_auto_retain_count}
        elif req.method == 'POST':
            return self.handle_int_POST(req,
                                        StorageConfig.BACKUP_AUTO_RETAIN_COUNT)
        else:
            raise exc.HTTPMethodNotAllowed()

    def handle_user(self, req):
        if req.method == 'GET':
            return {'value':self.sc.backup_user_retain_count}
        elif req.method == 'POST':
            return self.handle_int_POST(req,
                                        StorageConfig.BACKUP_USER_RETAIN_COUNT)
        else:
            raise exc.HTTPMethodNotAllowed()

    def handle_logs(self, req):
        if req.method == 'GET':
            return {'value':self.sc.log_archive_retain_count}
        elif req.method == 'POST':
            return self.handle_int_POST(req,
                                        StorageConfig.LOG_ARCHIVE_RETAIN_COUNT)
        else:
            raise exc.HTTPMethodNotAllowed()

    def handle_twb(self, req):
        if req.method == 'GET':
            return {'value':self.sc.workbooks_as_twb}
        elif req.method == 'POST':
            return self.handle_yesno_POST(req, StorageConfig.WORKBOOKS_AS_TWB)
        else:
            raise exc.HTTPMethodNotAllowed()

    @required_role(Role.MANAGER_ADMIN)
    def handle(self, req):
        path_info = self.base_path_info(req)
        if path_info == 'encryption':
            return self.handle_encryption(req)
        elif path_info == 'dest':
            return self.handle_dest(req)
        elif path_info == 'low':
            return self.handle_low(req)
        elif path_info == 'high':
            return self.handle_high(req)
        elif path_info == 'auto':
            return self.handle_auto(req)
        elif path_info == 'user':
            return self.handle_user(req)
        elif path_info == 'logs':
            return self.handle_logs(req)
        elif path_info == 'twb':
            return self.handle_twb(req)

        if req.method == "GET":
            return self.handle_get(req)

        raise exc.HTTPBadRequest()

class StoragePage(PalettePage):
    TEMPLATE = "storage.mako"
    active = 'storage'
    expanded = True
    required_role = Role.MANAGER_ADMIN

def make_storage(global_conf):
    return StoragePage(global_conf)
