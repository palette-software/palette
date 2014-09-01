from webob import exc

from akiri.framework.ext.sqlalchemy import meta

from controller.profile import Role
from controller.agent import Agent
from controller.util import sizestr, str2bool
from controller.storage import StorageConfig
from controller.files import FileManager

from controller.agentinfo import AgentVolumesEntry
from controller.cloud import CloudManager
import ntpath, posixpath

from page import PalettePage
from rest import PaletteRESTHandler, required_parameters, required_role

__all__ = ["StorageApplication"]

class StorageApplication(PaletteRESTHandler):
    NAME = 'storage'

    LOW_WATERMARK_RANGE = [50, 55, 60, 65, 70, 75, 80, 85, 90, 95]
    HIGH_WATERMARK_RANGE = [50, 55, 60, 65, 70, 75, 80, 85, 90, 95]
    HTTP_LOAD_WARN_RANGE = [0, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30, 35, 40, 45]
    HTTP_LOAD_ERROR_RANGE = [0, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30, 35, 40, 45]
    HTTP_LOAD_WARN_MAX = 45
    HTTP_LOAD_ERROR_MAX = 45

    def build_item_for_volume(self, volume):
        fmt = "%s %s %s (%s Unused)"
        name = volume.name
        if volume.agent.iswin and len(name) == 1:
            name = name + ':'
        return fmt % (volume.agent.displayname, name,
                      sizestr(volume.size), sizestr(volume.available_space))

    def build_item_for_web_request(self, x):
        if x == 0:
            return 'Do not monitor'
        if x == 1:
            return '1 second'
        return '%d seconds' % x

    def handle_get(self, req):
        sc = StorageConfig(req.system)
        data = {StorageConfig.STORAGE_ENCRYPT: sc.storage_encrypt,
                StorageConfig.WORKBOOKS_AS_TWB: sc.workbooks_as_twb}

        # populate the storage destination type
        dest = {'name': 'storage-destination'}
        options = []

        value = None
        destid = self.destid(sc)
        for volume in AgentVolumesEntry.get_archives_by_envid(req.envid):
            item = self.build_item_for_volume(volume)
            ourid = '%s:%d' % (FileManager.STORAGE_TYPE_VOL, volume.volid)
            options.append({'id': ourid, 'item':item})
            if destid == ourid:
                value = item

        for entry in CloudManager.get_clouds_by_envid(req.envid):
            item = CloudManager.text(entry.cloud_type)
            ourid = '%s:%d' % (FileManager.STORAGE_TYPE_CLOUD, entry.cloudid)
            options.append({'id': ourid, 'item': item})

            if destid == ourid:
                value = item

        if not options:
            # Placeholder until an agent connects.
            value = sc.text(FileManager.STORAGE_TYPE_VOL)
            options.append({'id': FileManager.STORAGE_TYPE_VOL,
                            'item': value})

        if value is None:
            value = sc.text(destid)

        dest['value'] = value
        dest['options'] = options

        low = {'name': StorageConfig.WATERMARK_LOW,
               'value': str(sc.watermark_low)}
        options = []
        for x in self.LOW_WATERMARK_RANGE:
            options.append({'id':x, 'item': str(x)})
        low['options'] = options

        high = {'name': StorageConfig.WATERMARK_HIGH,
               'value': str(sc.watermark_high)}
        options = []
        for x in self.HIGH_WATERMARK_RANGE:
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

        value = self.build_item_for_web_request(sc.http_load_warn)
        http_load_warn = {'name': StorageConfig.HTTP_LOAD_WARN, 'value': value}

        options = []
        for x in self.HTTP_LOAD_WARN_RANGE:
            item = self.build_item_for_web_request(x)
            options.append({'id':x, 'item': item})
        http_load_warn['options'] = options

        value = self.build_item_for_web_request(sc.http_load_error)
        http_load_error = {'name': StorageConfig.HTTP_LOAD_ERROR,
                           'value': value}

        options = []
        for x in self.HTTP_LOAD_ERROR_RANGE:
            item = self.build_item_for_web_request(x)
            options.append({'id':x, 'item': item})
        http_load_error['options'] = options

        data['config'] = [dest, low, high, auto, user, logs, http_load_warn, http_load_error]
        return data

    @required_parameters('value')
    def handle_yesno_POST(self, req, name):
        value = str2bool(req.POST['value'])
        s = value and 'yes' or 'no'
        req.system.save(name, s)
        return {'value':value}

    def handle_encryption(self, req):
        if req.method == 'GET':
            sc = StorageConfig(req.system)
            return {'value':sc.storage_encrypt}
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
        req.system.save(StorageConfig.BACKUP_DEST_ID, destid)
        req.system.save(StorageConfig.BACKUP_DEST_TYPE, desttype)
        return {'id':value}

    # return the id of the current selection (built from StorageConfig)
    def destid(self, sc):
        dest_id = sc.backup_dest_id
        if dest_id == None:
            dest_id = 0

        value = sc.backup_dest_type
        return "%s:%d" % (sc.backup_dest_type, dest_id)

    def handle_dest(self, req):
        sc = StorageConfig(req.system)
        if req.method == 'GET':
            return {'id':self.destid(sc)}
        elif req.method == 'POST':
            return self.handle_dest_POST(req)
        else:
            raise exc.HTTPMethodNotAllowed()

    @required_parameters('id')
    def handle_int_POST(self, req, name):
        value = req.POST['id']
        req.system.save(name, str(value))
        return {'id':value}

    def handle_low(self, req):
        sc = StorageConfig(req.system)
        if req.method == 'GET':
            return {'value':sc.watermark_low}
        elif req.method == 'POST':
            d = self.handle_int_POST(req, StorageConfig.WATERMARK_LOW)
            self.telnet.send_cmd('info all', req=req)
            return d
        else:
            raise exc.HTTPMethodNotAllowed()

    def handle_high(self, req):
        sc = StorageConfig(req.system)
        if req.method == 'GET':
            return {'value':sc.watermark_high}
        elif req.method == 'POST':
            d = self.handle_int_POST(req, StorageConfig.WATERMARK_HIGH)
            self.telnet.send_cmd('info all', req=req)
            return d
        else:
            raise exc.HTTPMethodNotAllowed()

    def handle_auto(self, req):
        sc = StorageConfig(req.system)
        if req.method == 'GET':
            return {'value':sc.backup_auto_retain_count}
        elif req.method == 'POST':
            return self.handle_int_POST(req,
                                        StorageConfig.BACKUP_AUTO_RETAIN_COUNT)
        else:
            raise exc.HTTPMethodNotAllowed()

    def handle_user(self, req):
        sc = StorageConfig(req.system)
        if req.method == 'GET':
            return {'value':sc.backup_user_retain_count}
        elif req.method == 'POST':
            return self.handle_int_POST(req,
                                        StorageConfig.BACKUP_USER_RETAIN_COUNT)
        else:
            raise exc.HTTPMethodNotAllowed()

    def handle_logs(self, req):
        sc = StorageConfig(req.system)
        if req.method == 'GET':
            return {'value':sc.log_archive_retain_count}
        elif req.method == 'POST':
            return self.handle_int_POST(req,
                                        StorageConfig.LOG_ARCHIVE_RETAIN_COUNT)
        else:
            raise exc.HTTPMethodNotAllowed()

    def handle_twb(self, req):
        sc = StorageConfig(req.system)
        if req.method == 'GET':
            return {'value':sc.workbooks_as_twb}
        elif req.method == 'POST':
            return self.handle_yesno_POST(req, StorageConfig.WORKBOOKS_AS_TWB)
        else:
            raise exc.HTTPMethodNotAllowed()

    def handle_load_warn(self, req):
        if req.method == 'GET':
            return {'value':self.sc.http_load_warn}
        elif req.method == 'POST':
            d = self.handle_int_POST(req, StorageConfig.HTTP_LOAD_WARN)
            return d
        else:
            raise exc.HTTPMethodNotAllowed()

    def handle_load_error(self, req):
        if req.method == 'GET':
            return {'value':self.sc.http_load_error}
        elif req.method == 'POST':
            d = self.handle_int_POST(req, StorageConfig.HTTP_LOAD_ERROR)
            return d
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
        elif path_info == 'http_load_warn':
            return self.handle_load_warn(req)
        elif path_info == 'http_load_error':
            return self.handle_load_error(req)

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
