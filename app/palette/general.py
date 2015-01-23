import time

from webob import exc

from akiri.framework.route import Router

from controller.profile import Role
from controller.util import sizestr, str2bool, extend
from controller.general import SystemConfig
from controller.files import FileManager
from controller.agent import AgentVolumesEntry
from controller.cloud import CloudManager, CloudEntry
from controller.passwd import set_aes_key_file
from controller.palapi import CommException

from .option import ListOption
from .page import PalettePage, FAKEPW
from .rest import required_parameters, required_role, PaletteRESTApplication
from .s3 import S3Application
from .gcs import GCSApplication
from .workbooks import CredentialMixin

class GeneralS3Application(PaletteRESTApplication, S3Application):
    """Handler for the 'STORAGE LOCATION' S3 section."""
    def service_GET(self, req):
        if 'action' in req.environ:
            raise exc.HTTPNotFound()
        return self.get_req(req)

    @required_parameters('access-key', 'secret-key', 'url')
    def save(self, req):
        print req.POST
        return self.cloud_save(req)

    @required_parameters('access-key', 'secret-key', 'url')
    def test(self, req):
        try:
            self.commapp.send_cmd('s3 test', req=req)
        except CommException:
            return {'status': 'FAIL'}
        return {'status': 'OK'}

    @required_parameters('access-key', 'secret-key', 'url')
    def remove(self, req):
        print req.POST
        return self.cloud_remove(req)

    @required_parameters('action')
    def service_POST(self, req):
        action = req.params_get('action')
        if action == 'save':
            return self.save(req)
        if action == 'test':
            return self.test(req)
        if action == 'remove':
            return self.remove(req)
        raise exc.HTTPBadRequest(req)

class GeneralGCSApplication(PaletteRESTApplication, GCSApplication):
    """Handler for the 'STORAGE LOCATION' GCS section."""
    def service_GET(self, req):
        if 'action' in req.environ:
            raise exc.HTTPNotFound()
        return self.get_req(req)

    @required_parameters('access-key', 'secret-key', 'url')
    def save(self, req):
        print req.POST
        return self.cloud_save(req)

    @required_parameters('access-key', 'secret-key', 'url')
    def test(self, req):
        try:
            self.commapp.send_cmd('gcs test', req=req)
        except CommException:
            return {'status': 'FAIL'}
        return {'status': 'OK'}

    def remove(self, req):
        print req.POST
        return self.cloud_remove(req)

    @required_parameters('action')
    def service_POST(self, req):
        action = req.params_get('action')
        if action == 'save':
            return self.save(req)
        if action == 'test':
            return self.test(req)
        if action == 'remove':
            print 'remove'
            return self.remove(req)
        raise exc.HTTPBadRequest(req)

class GeneralLocalApplication(PaletteRESTApplication):
    """Handler for the 'STORAGE LOCATION' My Machine section."""

    def build_item_for_volume(self, volume):
        fmt = "%s %s %s free of %s"
        name = volume.name
        if volume.agent.iswin and len(name) == 1:
            name = name + ':'
        return fmt % (volume.agent.displayname, name,
                      sizestr(volume.available_space), sizestr(volume.size))

    def destid(self, scfg):
        """Return the id of the current selection (built from SystemConfig)."""
        dest_id = scfg.backup_dest_id
        if dest_id == None:
            dest_id = 0

        return "%s:%d" % (scfg.backup_dest_type, dest_id)

    def service_GET(self, req):
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

        if not options:
            # Placeholder until an agent connects.
            value = scfg.text(FileManager.STORAGE_TYPE_VOL)
            options.append({'id': FileManager.STORAGE_TYPE_VOL,
                            'item': value})

        if value is None:
            value = scfg.text(FileManager.STORAGE_TYPE_VOL)

        dest['value'] = value
        dest['options'] = options

        data['config'] = [dest]
        return data

    def service_POST(self, req):
        # pylint: disable=unused-argument
        print 'post', req
        return {}

        # Fixme: Add something like the following after the js is finished
        value = req.POST['id']
        parts = value.split(':')
        if len(parts) != 2:
            print "Bad value:", value
            raise exc.HTTPBadRequest()

        (desttype, destid) = parts
        req.system.save(SystemConfig.BACKUP_DEST_ID, destid)
        req.system.save(SystemConfig.BACKUP_DEST_TYPE, desttype)
        return {'id':value}

class _GeneralStorageApplication(PaletteRESTApplication):
    """Overall GET handler for /rest/general/storage"""
    def __init__(self):
        super(_GeneralStorageApplication, self).__init__()
        self.gcs = GeneralGCSApplication()
        self.local = GeneralLocalApplication()
        # pylint: disable=invalid-name
        self.s3 = GeneralS3Application()

    def service_GET(self, req):
        scfg = SystemConfig(req.system)
        data = {}
        dest_type = scfg.backup_dest_type
        if dest_type == FileManager.STORAGE_TYPE_VOL:
            data['storage-type'] = 'local'
        elif dest_type == FileManager.STORAGE_TYPE_CLOUD:
            dest_id = scfg.backup_dest_id
            entry = CloudEntry.get_by_envid_cloudid(req.envid, dest_id)
            data['storage-type'] = entry.cloud_type

        extend(data, self.s3.service_GET(req))
        extend(data, self.gcs.service_GET(req))

        # FIXME: return data based on type return values
        # FIXME: local - needs options for 'storage-destination'.
        # FIXME: s3/gcs - access-key, secret-key, url
        extend(data, self.local.service_GET(req))
        print "data:", data
        return data


class GeneralStorageApplication(Router):
    """Main handler/router for 'STORAGE LOCATION' section."""
    def __init__(self):
        super(GeneralStorageApplication, self).__init__()
        self.add_route(r'/\Z', _GeneralStorageApplication())
        self.add_route(r'/s3(/(?P<action>[^\s]+))?\Z', GeneralS3Application())
        self.add_route(r'/gcs(/(?P<action>[^\s]+))?\Z', GeneralGCSApplication())
        self.add_route(r'/local\Z', GeneralLocalApplication())


class GeneralBackupApplication(PaletteRESTApplication):
    """Handler for the 'BACKUPS' section."""
    SCHEDULED_BACKUP_PERIOD_RANGE = [1, 2, 3, 4, 6, 8, 12, 24]
    SCHEDULED_BACKUP_HOUR_RANGE = range(1, 12)
    SCHEDULED_BACKUP_MINUTE_RANGE = ['00', '15', '30', '45']
    SCHEDULED_BACKUP_RETAIN_RANGE = [7, 14, 21, 28]
    USER_BACKUP_RETAIN_RANGE = range(1, 11)

    def service_GET(self, req):
        scfg = SystemConfig(req.system)

        config = [ListOption(SystemConfig.SCHEDULED_BACKUP_PERIOD,
                             scfg.scheduled_backup_period,
                             self.SCHEDULED_BACKUP_PERIOD_RANGE),
                  ListOption(SystemConfig.BACKUP_AUTO_RETAIN_COUNT,
                             scfg.backup_auto_retain_count,
                             self.SCHEDULED_BACKUP_RETAIN_RANGE),
                  ListOption(SystemConfig.BACKUP_USER_RETAIN_COUNT,
                             scfg.backup_user_retain_count,
                             self.USER_BACKUP_RETAIN_RANGE),
                  ListOption(SystemConfig.SCHEDULED_BACKUP_HOUR,
                             scfg.scheduled_backup_hour,
                             self.SCHEDULED_BACKUP_HOUR_RANGE),
                  ListOption(SystemConfig.SCHEDULED_BACKUP_MINUTE,
                             scfg.scheduled_backup_minute,
                             self.SCHEDULED_BACKUP_MINUTE_RANGE),
                  ListOption(SystemConfig.SCHEDULED_BACKUP_AMPM,
                             scfg.scheduled_backup_ampm,
                             ['AM', 'PM'])]

        data = {}
        data['config'] = [option.default() for option in config]
        data['schedule-backups'] = scfg.scheduled_backup_enabled
        data['timezone'] = time.strftime("%Z")
        return data


class EmailAlertApplication(PaletteRESTApplication):
    """Handler for the 'EMAIL ALERTS' section."""
    def service_GET(self, req):
        scfg = SystemConfig(req.system)
        data = {}
        data['alert-admins'] = scfg.alerts_admin_enabled
        data['alert-publishers'] = scfg.alerts_publisher_enabled
        return data

    # FIXME: finish POST
    def service_POST(self, req):
        print 'alert', req

        return

        # Fixme: Add something like the following after the js is finished
        value = req.POST['id']
        parts = value.split(':')
        if len(parts) != 2:
            print "Bad value:", value
            raise exc.HTTPBadRequest()

        (desttype, destid) = parts
        req.system.save(SystemConfig.BACKUP_DEST_ID, destid)
        req.system.save(SystemConfig.BACKUP_DEST_TYPE, desttype)
        return {'id':value}


class GeneralZiplogApplication(PaletteRESTApplication):
    """Handler for the 'ZIPLOGSS' section."""
    SCHEDULED_RETAIN_RANGE = range(1, 10)
    USER_RETAIN_RANGE = range(1, 10)

    def service_GET(self, req):
        # pylint: disable=unused-argument

        scfg = SystemConfig(req.system)

        config = [ListOption(SystemConfig.ZIPLOG_AUTO_RETAIN_COUNT,
                             scfg.ziplog_auto_retain_count,
                             self.SCHEDULED_RETAIN_RANGE),
                  ListOption(SystemConfig.ZIPLOG_USER_RETAIN_COUNT,
                             scfg.ziplog_user_retain_count,
                             self.USER_RETAIN_RANGE)]
        data = {}
        data['config'] = [option.default() for option in config]
        data['schedule-ziplogs'] = scfg.scheduled_ziplog_enabled
        return data


class GeneralArchiveApplication(PaletteRESTApplication):
    """Handler for 'WORKBOOK ARCHIVE' section."""
    def service_GET(self, req):
        # pylint: disable=unused-argument
        scfg = SystemConfig(req.system)

        data = {}
        data['username'] = scfg.archive_username
        data['password'] = '*' * len(scfg.archive_password)
        data['archive'] = scfg.archive_enabled
        return data


# Maybe break this into Storage, CPU, Workbook?
class GeneralMonitorApplication(PaletteRESTApplication):
    """Handler from 'MONITORING' section."""
    def service_GET(self, req):
        # pylint: disable=unused-argument
        scfg = SystemConfig(req.system)

        # FIXME: make each of these an option in config, not just values.
        # FIXME: also allow them not to be set in the system table.
        data = {}
        data['storage-warning'] = scfg.watermark_low
        data['storage-error'] = scfg.watermark_high

        data['cpu-warning'] = scfg.cpu_load_warn
        data['cpu-error'] = scfg.cpu_load_error
        data['cpu-period-warn'] = scfg.cpu_period_warn
        data['cpu-period-error'] = scfg.cpu_period_error

        data['workbook-warn'] = scfg.workbook_load_warn
        data['workbook-error'] = scfg.workbook_load_error

        return data


class OldGeneralApplication(PaletteRESTApplication):
    NAME = 'general'

    LOW_WATERMARK_RANGE = [50, 55, 60, 65, 70, 75, 80, 85, 90, 95]
    HIGH_WATERMARK_RANGE = [50, 55, 60, 65, 70, 75, 80, 85, 90, 95]
    HTTP_LOAD_WARN_RANGE = [0, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30, 35, 40, 45]
    HTTP_LOAD_ERROR_RANGE = [0, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30, 35, 40, 45]
    CPU_LOAD_WARN_RANGE = [50, 55, 60, 65, 70, 75, 80, 85, 90, 95]
    CPU_LOAD_ERROR_RANGE = [50, 55, 60, 65, 70, 75, 80, 85, 90, 95]
    CPU_PERIOD_WARN_RANGE = [1, 2, 3, 4, 5, 10, 15, 20, 25, 30]
    CPU_PERIOD_ERROR_RANGE = [1, 2, 3, 4, 5, 10, 15, 20, 25, 30]

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

        gcs_id = scfg.gcs_id
        s3_id = scfg.s3_id

        for entry in CloudEntry.get_all_by_envid(req.envid):
            # An enabled (non-deleted) cloud entry are the ones
            # referred to in the system table.
            if S3Application.NAME == entry.cloud_type and \
                                                        s3_id != entry.cloudid:
                continue
            if GCSApplication.NAME == entry.cloud_type and \
                                                        gcs_id != entry.cloudid:
                continue

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
            value = scfg.text(FileManager.STORAGE_TYPE_VOL)

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

        cpu_load_warn = {'name': SystemConfig.CPU_LOAD_WARN,
                         'value': str(scfg.cpu_load_warn)}
        options = []
        for x in self.CPU_LOAD_WARN_RANGE:
            options.append({'id':x, 'item': str(x)})
        cpu_load_warn['options'] = options

        cpu_load_error = {'name': SystemConfig.CPU_LOAD_ERROR,
                          'value': str(scfg.cpu_load_error)}
        options = []
        for x in self.CPU_LOAD_ERROR_RANGE:
            options.append({'id':x, 'item': str(x)})
        cpu_load_error['options'] = options

        cpu_period_warn = {'name': SystemConfig.CPU_PERIOD_WARN,
                           'value': str(scfg.cpu_period_warn / 60)}
        options = []
        for x in self.CPU_PERIOD_WARN_RANGE:
            options.append({'id':x * 60, 'item': str(x)})
        cpu_period_warn['options'] = options

        cpu_period_error = {'name': SystemConfig.CPU_PERIOD_ERROR,
                            'value': str(scfg.cpu_period_error / 60)}
        options = []
        for x in self.CPU_PERIOD_ERROR_RANGE:
            options.append({'id':x * 60, 'item': str(x)})
        cpu_period_error['options'] = options

        data['config'] = [dest, low, high, auto, user, logs,
                          http_load_warn, http_load_error,
                          cpu_load_warn, cpu_load_error,
                          cpu_period_warn, cpu_period_error]
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

    def _handle_load_warn(self, req):
        scfg = SystemConfig(req.system)
        if req.method == 'GET':
            return {'value':scfg.http_load_warn}
        elif req.method == 'POST':
            d = self.handle_int_POST(req, SystemConfig.HTTP_LOAD_WARN)
            return d
        else:
            raise exc.HTTPMethodNotAllowed()

    def _handle_load_error(self, req):
        scfg = SystemConfig(req.system)
        if req.method == 'GET':
            return {'value':scfg.http_load_error}
        elif req.method == 'POST':
            d = self.handle_int_POST(req, SystemConfig.HTTP_LOAD_ERROR)
            return d
        else:
            raise exc.HTTPMethodNotAllowed()

    def _handle_cpu_load_warn(self, req):
        scfg = SystemConfig(req.system)
        if req.method == 'GET':
            return {'value':scfg.cpu_load_warn}
        elif req.method == 'POST':
            d = self.handle_int_POST(req, SystemConfig.CPU_LOAD_WARN)
            return d
        else:
            raise exc.HTTPMethodNotAllowed()

    def _handle_cpu_load_error(self, req):
        scfg = SystemConfig(req.system)
        if req.method == 'GET':
            return {'value':scfg.cpu_load_error}
        elif req.method == 'POST':
            d = self.handle_int_POST(req, SystemConfig.CPU_LOAD_ERROR)
            return d
        else:
            raise exc.HTTPMethodNotAllowed()

    def _handle_cpu_period_warn(self, req):
        scfg = SystemConfig(req.system)
        if req.method == 'GET':
            return {'value':scfg.cpu_period_warn}
        elif req.method == 'POST':
            d = self.handle_int_POST(req, SystemConfig.CPU_PERIOD_WARN)
            return d
        else:
            raise exc.HTTPMethodNotAllowed()

    def _handle_cpu_period_error(self, req):
        scfg = SystemConfig(req.system)
        if req.method == 'GET':
            return {'value':scfg.cpu_period_error}
        elif req.method == 'POST':
            d = self.handle_int_POST(req, SystemConfig.CPU_PERIOD_ERROR)
            return d
        else:
            raise exc.HTTPMethodNotAllowed()

    @required_role(Role.MANAGER_ADMIN)
    def service(self, req):
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches
        if 'action' in req.environ:
            action = req.environ['action']
            if action == 'encryption':
                return self.handle_encryption(req)
            elif action == 'dest':
                return self.handle_dest(req)
            elif action == 'low':
                return self.handle_low(req)
            elif action == 'high':
                return self.handle_high(req)
            elif action == 'auto':
                return self.handle_auto(req)
            elif action == 'user':
                return self.handle_user(req)
            elif action == 'logs':
                return self.handle_logs(req)
            elif action == 'twb':
                return self.handle_twb(req)
            elif action == 'http_load_warn' or action == 'http/load/warn':
                return self._handle_load_warn(req)
            elif action == 'http_load_error' or action == 'http/load/error':
                return self._handle_load_error(req)
            elif action == 'cpu/load/warn':
                return self._handle_cpu_load_warn(req)
            elif action == 'cpu/load/error':
                return self._handle_cpu_load_error(req)
            elif action == 'cpu/period/warn':
                return self._handle_cpu_period_warn(req)
            elif action == 'cpu/period/error':
                return self._handle_cpu_period_error(req)
            raise exc.HTTPNotFound()

        if req.method != "GET":
            raise exc.HTTPMethodNotAllowed()

        return self.handle_get(req)


class _GeneralApplication(PaletteRESTApplication):

    def __init__(self):
        super(_GeneralApplication, self).__init__()
        self.backup = GeneralBackupApplication()
        self.email_alert = EmailAlertApplication()
        self.ziplog = GeneralZiplogApplication()
        self.archive = GeneralArchiveApplication()
        self.storage = _GeneralStorageApplication() # Don't use the Router
        self.monitor = GeneralMonitorApplication()

    def service_GET(self, req):
        data = {}
        extend(data, self.backup.service_GET(req))
        extend(data, self.email_alert.service_GET(req))
        extend(data, self.ziplog.service_GET(req))
        extend(data, self.archive.service_GET(req))
        extend(data, self.storage.service_GET(req))
        # FIXME: uncomment
        # extend(data, self.monitor.service_GET(req))
        return data


class GeneralApplication(Router):
    """Main handler/router for /rest/general"""
    def __init__(self):
        super(GeneralApplication, self).__init__()
        self.add_route(r'/\Z', _GeneralApplication())
        self.add_route(r'/storage\Z|/storage/', GeneralStorageApplication())
        self.add_route(r'/email/alerts?\Z', EmailAlertApplication())
        self.add_route(r'/backup\Z', GeneralBackupApplication())
        self.add_route(r'/ziplog\Z', GeneralZiplogApplication())
        self.add_route(r'/monitor\Z', GeneralMonitorApplication())
        self.add_route(r'/archive\Z|/workbook-archive\Z|/workbook\Z',
                       GeneralArchiveApplication())


class GeneralPage(PalettePage, CredentialMixin):
    TEMPLATE = "config/general.mako"
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
