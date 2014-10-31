from webob import exc

from controller.profile import Role
from controller.util import sizestr, str2bool
from controller.general import SystemConfig
from controller.files import FileManager
from controller.agent import AgentVolumesEntry
from controller.cloud import CloudManager, CloudEntry
from controller.passwd import set_aes_key_file

from page import PalettePage, FAKEPW
from rest import PaletteRESTHandler, required_parameters, required_role

from workbooks import CredentialMixin

__all__ = ["GeneralApplication"]

class GeneralApplication(PaletteRESTHandler):
    NAME = 'general'

    LOW_WATERMARK_RANGE = [50, 55, 60, 65, 70, 75, 80, 85, 90, 95]
    HIGH_WATERMARK_RANGE = [50, 55, 60, 65, 70, 75, 80, 85, 90, 95]
    HTTP_LOAD_WARN_RANGE = [0, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30, 35, 40, 45]
    HTTP_LOAD_ERROR_RANGE = [0, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30, 35, 40, 45]

    def build_item_for_volume(self, volume):
        fmt = "%s %s %s free of %s"
        name = volume.name
        if volume.agent.iswin and len(name) == 1:
            name = name + ':'
        return fmt % (volume.agent.displayname, name,
                      sizestr(volume.available_space), sizestr(volume.size))

    def build_item_for_web_request(self, x):
        if x == 0:
            return 'Do not monitor'
        if x == 1:
            return '1 second'
        return '%d seconds' % x

    def handle_get(self, req):
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        scfg = SystemConfig(req.system)
        data = {SystemConfig.STORAGE_ENCRYPT: scfg.storage_encrypt,
                SystemConfig.WORKBOOKS_AS_TWB: scfg.workbooks_as_twb}

        # populate the storage destination type
        dest = {'name': 'storage-destination'}
        options = []

        value = None
        destid = self.destid(scfg)
        for volume in AgentVolumesEntry.get_archives_by_envid(req.envid):
            item = self.build_item_for_volume(volume)
            ourid = '%s:%d' % (FileManager.STORAGE_TYPE_VOL, volume.volid)
            options.append({'id': ourid, 'item':item})
            if destid == ourid:
                value = item

        for entry in CloudEntry.get_all_by_envid(req.envid):
            item = CloudManager.text(entry.cloud_type)
            ourid = '%s:%d' % (FileManager.STORAGE_TYPE_CLOUD, entry.cloudid)
            options.append({'id': ourid, 'item': item})

            if destid == ourid:
                value = item

        if not options:
            # Placeholder until an agent connects.
            value = scfg.text(FileManager.STORAGE_TYPE_VOL)
            options.append({'id': FileManager.STORAGE_TYPE_VOL,
                            'item': value})

        if value is None:
            value = scfg.text(destid)

        dest['value'] = value
        dest['options'] = options

        low = {'name': SystemConfig.WATERMARK_LOW,
               'value': str(scfg.watermark_low)}
        options = []
        for x in self.LOW_WATERMARK_RANGE:
            options.append({'id':x, 'item': str(x)})
        low['options'] = options

        high = {'name': SystemConfig.WATERMARK_HIGH,
               'value': str(scfg.watermark_high)}
        options = []
        for x in self.HIGH_WATERMARK_RANGE:
            options.append({'id':x, 'item': str(x)})
        high['options'] = options

        auto = {'name': SystemConfig.BACKUP_AUTO_RETAIN_COUNT,
               'value': str(scfg.backup_auto_retain_count)}
        options = []
        for x in [7, 14, 21, 28]:
            options.append({'id':x, 'item': str(x)})
        auto['options'] = options

        options = []
        user = {'name': SystemConfig.BACKUP_USER_RETAIN_COUNT,
               'value': str(scfg.backup_user_retain_count)}
        for x in range(1, 11):
            options.append({'id':x, 'item': str(x)})
        user['options'] = options

        logs = {'name': SystemConfig.LOG_ARCHIVE_RETAIN_COUNT,
               'value': str(scfg.log_archive_retain_count)}
        options = []
        for x in range(1, 11):
            options.append({'id':x, 'item': str(x)})
        logs['options'] = options

        value = self.build_item_for_web_request(scfg.http_load_warn)
        http_load_warn = {'name': SystemConfig.HTTP_LOAD_WARN, 'value': value}

        options = []
        for x in self.HTTP_LOAD_WARN_RANGE:
            item = self.build_item_for_web_request(x)
            options.append({'id':x, 'item': item})
        http_load_warn['options'] = options

        value = self.build_item_for_web_request(scfg.http_load_error)
        http_load_error = {'name': SystemConfig.HTTP_LOAD_ERROR,
                           'value': value}

        options = []
        for x in self.HTTP_LOAD_ERROR_RANGE:
            item = self.build_item_for_web_request(x)
            options.append({'id':x, 'item': item})
        http_load_error['options'] = options

        data['config'] = [dest, low, high, auto, user, logs,
                          http_load_warn, http_load_error]
        return data

    @required_parameters('value')
    # pylint: disable=invalid-name
    def handle_yesno_POST(self, req, name):
        value = str2bool(req.POST['value'])
        req.system.save(name)
        return {'value':value}

    def handle_encryption(self, req):
        if req.method == 'GET':
            scfg = SystemConfig(req.system)
            return {'value':scfg.storage_encrypt}
        elif req.method == 'POST':
            return self.handle_yesno_POST(req, SystemConfig.STORAGE_ENCRYPT)
        else:
            raise exc.HTTPMethodNotAllowed()

    @required_parameters('id')
    # pylint: disable=invalid-name
    def handle_dest_POST(self, req):
        value = req.POST['id']
        parts = value.split(':')
        if len(parts) != 2:
            print "Bad value:", value
            raise exc.HTTPBadRequest()

        (desttype, destid) = parts
        req.system.save(SystemConfig.BACKUP_DEST_ID, destid)
        req.system.save(SystemConfig.BACKUP_DEST_TYPE, desttype)
        return {'id':value}

    # return the id of the current selection (built from SystemConfig)
    def destid(self, scfg):
        dest_id = scfg.backup_dest_id
        if dest_id == None:
            dest_id = 0

        return "%s:%d" % (scfg.backup_dest_type, dest_id)

    def handle_dest(self, req):
        scfg = SystemConfig(req.system)
        if req.method == 'GET':
            return {'id':self.destid(scfg)}
        elif req.method == 'POST':
            return self.handle_dest_POST(req)
        else:
            raise exc.HTTPMethodNotAllowed()

    @required_parameters('id')
    # pylint: disable=invalid-name
    def handle_int_POST(self, req, name):
        value = req.POST['id']
        req.system.save(name, str(value))
        return {'id':value}

    def handle_low(self, req):
        scfg = SystemConfig(req.system)
        if req.method == 'GET':
            return {'value':scfg.watermark_low}
        elif req.method == 'POST':
            d = self.handle_int_POST(req, SystemConfig.WATERMARK_LOW)
            self.commapp.send_cmd('info all', req=req, read_response=False)
            return d
        else:
            raise exc.HTTPMethodNotAllowed()

    def handle_high(self, req):
        scfg = SystemConfig(req.system)
        if req.method == 'GET':
            return {'value':scfg.watermark_high}
        elif req.method == 'POST':
            d = self.handle_int_POST(req, SystemConfig.WATERMARK_HIGH)
            self.commapp.send_cmd('info all', req=req, read_response=False)
            return d
        else:
            raise exc.HTTPMethodNotAllowed()

    def handle_auto(self, req):
        scfg = SystemConfig(req.system)
        if req.method == 'GET':
            return {'value':scfg.backup_auto_retain_count}
        elif req.method == 'POST':
            return self.handle_int_POST(req,
                                        SystemConfig.BACKUP_AUTO_RETAIN_COUNT)
        else:
            raise exc.HTTPMethodNotAllowed()

    def handle_user(self, req):
        scfg = SystemConfig(req.system)
        if req.method == 'GET':
            return {'value':scfg.backup_user_retain_count}
        elif req.method == 'POST':
            return self.handle_int_POST(req,
                                        SystemConfig.BACKUP_USER_RETAIN_COUNT)
        else:
            raise exc.HTTPMethodNotAllowed()

    def handle_logs(self, req):
        scfg = SystemConfig(req.system)
        if req.method == 'GET':
            return {'value':scfg.log_archive_retain_count}
        elif req.method == 'POST':
            return self.handle_int_POST(req,
                                        SystemConfig.LOG_ARCHIVE_RETAIN_COUNT)
        else:
            raise exc.HTTPMethodNotAllowed()

    def handle_twb(self, req):
        scfg = SystemConfig(req.system)
        if req.method == 'GET':
            return {'value':scfg.workbooks_as_twb}
        elif req.method == 'POST':
            return self.handle_yesno_POST(req, SystemConfig.WORKBOOKS_AS_TWB)
        else:
            raise exc.HTTPMethodNotAllowed()

    def handle_load_warn(self, req):
        scfg = SystemConfig(req.system)
        if req.method == 'GET':
            return {'value':scfg.http_load_warn}
        elif req.method == 'POST':
            d = self.handle_int_POST(req, SystemConfig.HTTP_LOAD_WARN)
            return d
        else:
            raise exc.HTTPMethodNotAllowed()

    def handle_load_error(self, req):
        scfg = SystemConfig(req.system)
        if req.method == 'GET':
            return {'value':scfg.http_load_error}
        elif req.method == 'POST':
            d = self.handle_int_POST(req, SystemConfig.HTTP_LOAD_ERROR)
            return d
        else:
            raise exc.HTTPMethodNotAllowed()

    @required_role(Role.MANAGER_ADMIN)
    def handle(self, req):
        # pylint: disable=too-many-return-statements
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


class GeneralPage(PalettePage, CredentialMixin):
    TEMPLATE = "general.mako"
    active = 'general'
    expanded = True
    required_role = Role.MANAGER_ADMIN

    def render(self, req, obj=None):
        primary = self.get_cred(req.envid, self.PRIMARY_KEY)
        if primary:
            req.primary_user = primary.user
            req.primary_pw = primary.embedded and FAKEPW or ''
        else:
            req.primary_user = req.primary_pw = ''
        secondary = self.get_cred(req.envid, self.SECONDARY_KEY)
        if secondary:
            req.secondary_user = secondary.user
            req.secondary_pw = secondary.embedded and FAKEPW or ''
        else:
            req.secondary_user = req.secondary_pw = ''
        return super(GeneralPage, self).render(req, obj=obj)

def make_general(global_conf, aes_key_file=None):
    # FIXME: should be actually global.
    if aes_key_file:
        set_aes_key_file(aes_key_file)
    return GeneralPage(global_conf)
