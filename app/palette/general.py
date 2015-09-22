import time
from collections import OrderedDict

from webob import exc

from akiri.framework.route import Router
import akiri.framework.sqlalchemy as meta

from controller.profile import Role
from controller.util import sizestr, extend, str2bool
from controller.files import FileManager
from controller.agent import AgentVolumesEntry
from controller.cloud import CloudEntry
from controller.passwd import aes_encrypt, aes_decrypt
from controller.palapi import CommException
from controller.credential import CredentialEntry
from controller.email_limit import EmailLimitEntry
from controller.system import SystemKeys

from .option import ListOption, DictOption
from .page import PalettePage
from .rest import required_parameters, required_role, PaletteRESTApplication
from .s3 import S3Application
from .gcs import GCSApplication
from .mixin import CredentialMixin

class WorkbookRetention(DictOption):
    """Representation of the 'Workbook Retention' dropdown."""
    NAME = SystemKeys.WORKBOOK_RETAIN_COUNT
    ALL = 0

    def __init__(self, valueid):
        options = OrderedDict({})
        options[self.ALL] = 'All'
        for count in [2, 3, 4, 5, 10, 25]:
            options[count] = str(count)
        super(WorkbookRetention, self).__init__(self.NAME, valueid, options)


class DatasourceRetention(DictOption):
    """Representation of the 'Datasource Retention' dropdown."""
    NAME = SystemKeys.DATASOURCE_RETAIN_COUNT
    ALL = 0

    def __init__(self, valueid):
        options = OrderedDict({})
        options[self.ALL] = 'All'
        for count in [2, 3, 4, 5, 10, 25]:
            options[count] = str(count)
        super(DatasourceRetention, self).__init__(self.NAME, valueid, options)


class GeneralS3Application(PaletteRESTApplication, S3Application):
    """Handler for the 'STORAGE LOCATION' S3 section."""
    @required_role(Role.MANAGER_ADMIN)
    def service_GET(self, req):
        if 'action' in req.environ:
            raise exc.HTTPNotFound()
        entry_dict = self.get_req(req)
        if entry_dict:
            entry_dict['s3-secret-key'] = \
                                    aes_decrypt(entry_dict['s3-secret-key'])
        return entry_dict

    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('access-key', 'secret-key', 'url')
    def save(self, req):
        return self.cloud_save(req)

    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('access-key', 'secret-key', 'url')
    def test(self, req):
        try:
            self.commapp.send_cmd(
                '/access-key=%s /secret-key=%s /bucket=%s s3 test' % \
                (req.POST['access-key'], aes_encrypt(req.POST['secret-key']),
                 self.url_to_bucket(req.POST['url'])), req=req)
        except CommException as ex:
            err = str(ex)
            if err.find("(403) Forbidden") != -1:
                err = "Credentials invalid."
            return {'status': 'FAIL', 'error': err}
        return {'status': 'OK'}

    def remove(self, req):
        return self.cloud_remove(req)

    @required_role(Role.MANAGER_ADMIN)
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
    @required_role(Role.MANAGER_ADMIN)
    def service_GET(self, req):
        if 'action' in req.environ:
            raise exc.HTTPNotFound()
        entry_dict = self.get_req(req)
        if entry_dict:
            entry_dict['gcs-secret-key'] = \
                                    aes_decrypt(entry_dict['gcs-secret-key'])
        return entry_dict

    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('access-key', 'secret-key', 'url')
    def save(self, req):
        return self.cloud_save(req)

    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('access-key', 'secret-key', 'url')
    def test(self, req):
        try:
            self.commapp.send_cmd(
                '/access-key=%s /secret-key=%s /bucket=%s gcs test' % \
                (req.POST['access-key'], aes_encrypt(req.POST['secret-key']),
                 self.url_to_bucket(req.POST['url'])), req=req)
        except CommException as ex:
            err = str(ex)
            if err.find("(403) Forbidden") != -1:
                err = "Credentials invalid."
            return {'status': 'FAIL', 'error': ex}
        return {'status': 'OK'}

    @required_role(Role.MANAGER_ADMIN)
    def remove(self, req):
        return self.cloud_remove(req)

    @required_role(Role.MANAGER_ADMIN)
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

class GeneralLocalApplication(PaletteRESTApplication):
    """Handler for the 'STORAGE LOCATION' My Machine section."""

    def build_item_for_volume(self, volume):
        fmt = "%s %s %s free of %s"
        name = volume.name
        if volume.agent.iswin and len(name) == 1:
            name = name + ':'
        return fmt % (volume.agent.displayname, name,
                      sizestr(volume.available_space), sizestr(volume.size))

    def destid(self, req):
        """Return the id of the current selection."""
        dest_id = req.system[SystemKeys.BACKUP_DEST_ID]
        if dest_id is None:
            dest_id = 0

        return "%s:%d" % (req.system[SystemKeys.BACKUP_DEST_TYPE], dest_id)

    @required_role(Role.MANAGER_ADMIN)
    def service_GET(self, req):
        data = {}
        for key in (SystemKeys.STORAGE_ENCRYPT, SystemKeys.WORKBOOKS_AS_TWB):
            data[key] = req.system[key]

        # populate the storage destination type
        options = []

        value = None
        destid = self.destid(req)
        for volume in AgentVolumesEntry.get_archives_by_envid(req.envid):
            item = self.build_item_for_volume(volume)
            ourid = '%s:%d' % (FileManager.STORAGE_TYPE_VOL, volume.volid)
            options.append({'id': ourid, 'item':item})
            if destid == ourid:
                value = item

        # We don't know about any volumes yet
        if not options:
            return {}

        # There is no volume currently selected.
        if value is None:
            # Arbitrarily choose the first one.
            value = options[0]['item']
            destid = options[0]['id']

        dest = {'name': 'storage-destination',
                'value': value,
                'id': destid}

        dest['options'] = options
        data['config'] = [dest]

        return data

    @required_role(Role.MANAGER_ADMIN)
    def service_POST(self, req):
        # pylint: disable=unused-argument
        value = req.POST['storage-destination']
        parts = value.split(':')
        if len(parts) != 2:
            print "Bad value:", value
            raise exc.HTTPBadRequest()

        (desttype, destid) = parts
        req.system[SystemKeys.BACKUP_DEST_ID] = destid
        req.system[SystemKeys.BACKUP_DEST_TYPE] = desttype
        return {'storage-destination':value}


class _GeneralStorageApplication(PaletteRESTApplication):
    """Overall GET handler for /rest/general/storage"""
    def __init__(self):
        super(_GeneralStorageApplication, self).__init__()
        self.gcs = GeneralGCSApplication()
        self.local = GeneralLocalApplication()
        # pylint: disable=invalid-name
        self.s3 = GeneralS3Application()

    @required_role(Role.MANAGER_ADMIN)
    def service_GET(self, req):
        data = {}
        dest_type = req.system[SystemKeys.BACKUP_DEST_TYPE]
        if dest_type == FileManager.STORAGE_TYPE_VOL:
            data['storage-type'] = 'local'
        elif dest_type == FileManager.STORAGE_TYPE_CLOUD:
            dest_id = req.system[SystemKeys.BACKUP_DEST_ID]
            entry = CloudEntry.get_by_envid_cloudid(req.envid, dest_id)
            data['storage-type'] = entry.cloud_type

        extend(data, self.local.service_GET(req))
        extend(data, self.s3.service_GET(req))
        extend(data, self.gcs.service_GET(req))
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
    BACKUP_SCHEDULED_PERIOD_RANGE = [1, 2, 3, 4, 6, 8, 12, 24]
    BACKUP_SCHEDULED_HOUR_RANGE = range(1, 12)
    BACKUP_SCHEDULED_MINUTE_RANGE = ['00', '15', '30', '45']
    BACKUP_SCHEDULED_RETAIN_RANGE = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25]
    USER_BACKUP_RETAIN_RANGE = BACKUP_SCHEDULED_RETAIN_RANGE

    @required_role(Role.MANAGER_ADMIN)
    def service_GET(self, req):
        config = [ListOption(SystemKeys.BACKUP_SCHEDULED_PERIOD,
                             req.system[SystemKeys.BACKUP_SCHEDULED_PERIOD],
                             self.BACKUP_SCHEDULED_PERIOD_RANGE),
                  ListOption(SystemKeys.BACKUP_AUTO_RETAIN_COUNT,
                             req.system[SystemKeys.BACKUP_AUTO_RETAIN_COUNT],
                             self.BACKUP_SCHEDULED_RETAIN_RANGE),
                  ListOption(SystemKeys.BACKUP_USER_RETAIN_COUNT,
                             req.system[SystemKeys.BACKUP_USER_RETAIN_COUNT],
                             self.USER_BACKUP_RETAIN_RANGE),
                  ListOption(SystemKeys.BACKUP_SCHEDULED_HOUR,
                             req.system[SystemKeys.BACKUP_SCHEDULED_HOUR],
                             self.BACKUP_SCHEDULED_HOUR_RANGE),
                  ListOption(SystemKeys.BACKUP_SCHEDULED_MINUTE,
                             req.system[SystemKeys.BACKUP_SCHEDULED_MINUTE],
                             self.BACKUP_SCHEDULED_MINUTE_RANGE),
                  ListOption(SystemKeys.BACKUP_SCHEDULED_AMPM,
                             req.system[SystemKeys.BACKUP_SCHEDULED_AMPM],
                             ['AM', 'PM'])
              ]

        scheduled_enabled = req.system[SystemKeys.BACKUP_SCHEDULED_ENABLED]

        data = {}
        data['config'] = [option.default() for option in config]
        data['scheduled-backups'] = scheduled_enabled
        data['timezone'] = time.strftime("%Z")
        return data

    @required_role(Role.MANAGER_ADMIN)
    def service_POST(self, req):
        if 'scheduled-backups' in req.POST:
            req.system[SystemKeys.BACKUP_SCHEDULED_ENABLED] = \
                                        str2bool(req.POST['scheduled-backups'])

        req.system[SystemKeys.BACKUP_AUTO_RETAIN_COUNT] = \
                                        req.POST['backup-auto-retain-count']
        req.system[SystemKeys.BACKUP_USER_RETAIN_COUNT] = \
                                        req.POST['backup-user-retain-count']
        meta.commit()
        return {}


class EmailAlertApplication(PaletteRESTApplication):
    """Handler for the 'EMAIL ALERTS' section."""
    @required_role(Role.MANAGER_ADMIN)
    def service_GET(self, req):
        data = {}
        data['alert-admins'] = req.system[SystemKeys.ALERTS_ADMIN_ENABLED]
        data['alert-publishers'] = \
                            req.system[SystemKeys.ALERTS_PUBLISHER_ENABLED]
        return data

    @required_role(Role.MANAGER_ADMIN)
    def service_POST(self, req):

        req.system[SystemKeys.ALERTS_PUBLISHER_ENABLED] = \
                            req.POST['alert-publishers']
        req.system[SystemKeys.ALERTS_ADMIN_ENABLED] = req.POST['alert-admins']

        if str2bool(req.POST['alert-publishers']) or \
                  str2bool(req.POST['alert-admins']):
            req.system[SystemKeys.EMAIL_SPIKE_DISABLED_ALERTS] = 'no'
            # does a session.commit()
            EmailLimitEntry.remove_all(req.envid)
        else:
            meta.commit()
        return {}


class GeneralZiplogApplication(PaletteRESTApplication):
    """Handler for the 'ZIPLOGSS' section."""
    SCHEDULED_RETAIN_RANGE = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25]
    USER_RETAIN_RANGE = SCHEDULED_RETAIN_RANGE

    @required_role(Role.MANAGER_ADMIN)
    def service_GET(self, req):
        # pylint: disable=unused-argument
        config = [ListOption(SystemKeys.ZIPLOG_AUTO_RETAIN_COUNT,
                             req.system[SystemKeys.ZIPLOG_AUTO_RETAIN_COUNT],
                             self.SCHEDULED_RETAIN_RANGE),
                  ListOption(SystemKeys.ZIPLOG_USER_RETAIN_COUNT,
                             req.system[SystemKeys.ZIPLOG_USER_RETAIN_COUNT],
                             self.USER_RETAIN_RANGE)
              ]

        enabled_scheduled = req.system[SystemKeys.ZIPLOG_SCHEDULED_ENABLED]

        data = {}
        data['config'] = [option.default() for option in config]
        data['schedule-ziplogs'] = enabled_scheduled
        return data

    @required_role(Role.MANAGER_ADMIN)
    def service_POST(self, req):
        if 'scheduled-ziplogs' in req.POST:
            req.system[SystemKeys.ZIPLOG_SCHEDULED_ENABLED] = \
                            req.POST['scheduled-ziplogs']

        req.system[SystemKeys.ZIPLOG_AUTO_RETAIN_COUNT] = \
                            req.POST['ziplog-auto-retain-count']
        req.system[SystemKeys.ZIPLOG_USER_RETAIN_COUNT] = \
                            req.POST['ziplog-user-retain-count']
        meta.commit()
        return {}

class GeneralArchiveApplication(PaletteRESTApplication, CredentialMixin):
    """Handler for 'ARCHIVE' section - both workbook and datasource settings."""

    @required_role(Role.MANAGER_ADMIN)
    def service_GET(self, req):
        # pylint: disable=unused-argument
        data = {}

        for key in (SystemKeys.WORKBOOK_ARCHIVE_ENABLED,
                    SystemKeys.DATASOURCE_ARCHIVE_ENABLED):
            data[key] = req.system[key]

        primary = self.get_cred(req.envid, self.PRIMARY_KEY)
        secondary = self.get_cred(req.envid, self.SECONDARY_KEY)
        if primary:
            data['archive-username'] = primary.user
            data['archive-password'] = primary.getpasswd()
        elif secondary:
            data['archive-username'] = secondary.user
            data['archive-password'] = secondary.getpasswd()
        else:
            data['archive-username'] = data['archive-password'] = ''

        valueid = req.system[SystemKeys.WORKBOOK_RETAIN_COUNT]
        workbook_retain_opts = WorkbookRetention(valueid)

        valueid = req.system[SystemKeys.DATASOURCE_RETAIN_COUNT]
        datasource_retain_opts = DatasourceRetention(valueid)

        data['config'] = [workbook_retain_opts.default(),
                          datasource_retain_opts.default()]
        return data

    @required_role(Role.MANAGER_ADMIN)
    def service_POST(self, req):
        for key in (SystemKeys.WORKBOOK_ARCHIVE_ENABLED,
                    SystemKeys.DATASOURCE_ARCHIVE_ENABLED,
                    SystemKeys.WORKBOOK_RETAIN_COUNT,
                    SystemKeys.DATASOURCE_RETAIN_COUNT):
            req.system[key] = req.POST[key]

        cred = self.get_cred(req.envid, self.PRIMARY_KEY)
        if not cred:
            cred = CredentialEntry(envid=req.envid, key=self.PRIMARY_KEY)
            meta.Session.add(cred)

        cred.user = req.POST['archive-username']
        cred.setpasswd(req.POST['archive-password'])

        meta.commit()
        return {}


# Maybe break this into Storage, CPU, Workbook?
class GeneralMonitorApplication(PaletteRESTApplication):
    """Handler from 'MONITORING' section."""

    LOW_WATERMARK_RANGE = [101, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95]
    HIGH_WATERMARK_RANGE = [101, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95]
    CPU_LOAD_WARN_RANGE = [101, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95]
    CPU_LOAD_ERROR_RANGE = [101, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95]
    CPU_PERIOD_WARN_RANGE = [1, 2, 3, 4, 5, 10, 15, 20, 25, 30]
    CPU_PERIOD_ERROR_RANGE = [1, 2, 3, 4, 5, 10, 15, 20, 25, 30]
    WORKBOOK_LOAD_WARN_RANGE = [0, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30,
                                35, 40, 45]
    WORKBOOK_LOAD_ERROR_RANGE = [0, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30,
                                 35, 40, 45]

    def build_item_for_web_request(self, seconds):
        if seconds == 0:
            return 'Do not monitor'
        if seconds == 1:
            return '1 second'
        return '%d seconds' % seconds

    @required_role(Role.MANAGER_ADMIN)
    def service_GET(self, req):
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches

        # FIXME: make every commented paragraph below a private method
        data = {}


        # watermark low
        watermark_low = req.system[SystemKeys.WATERMARK_LOW]
        if watermark_low > 100:
            low = {'name': SystemKeys.WATERMARK_LOW,
                   'value': "Do not monitor",
                   'id': watermark_low}
        else:
            low = {'name': SystemKeys.WATERMARK_LOW,
                   'value': "%d%%" % watermark_low,
                   'id': watermark_low}
        options = []
        for value in self.LOW_WATERMARK_RANGE:
            if value > 100:
                options.append({'id':value, 'item': "Do not monitor"})
            else:
                options.append({'id':value, 'item': "%s%%" % str(value)})
        low['options'] = options

        # watermark high
        watermark_high = req.system[SystemKeys.WATERMARK_HIGH]
        if watermark_high > 100:
            high = {'name': SystemKeys.WATERMARK_HIGH,
                   'value': "Do not monitor",
                   'id': watermark_high}
        else:
            high = {'name': SystemKeys.WATERMARK_HIGH,
                   'value': '%d%%' % watermark_high,
                   'id': watermark_high}
        options = []
        for value in self.HIGH_WATERMARK_RANGE:
            if value > 100:
                options.append({'id':value, 'item': 'Do not monitor'})
            else:
                options.append({'id':value, 'item': '%s%%' % str(value)})
        high['options'] = options

        # workbook warn (formerly http load warn)
        seconds = req.system[SystemKeys.HTTP_LOAD_WARN]
        value = self.build_item_for_web_request(seconds)
        workbook_load_warn = {'name': SystemKeys.HTTP_LOAD_WARN,
                              'value': value,
                              'id': seconds}

        options = []
        for value in self.WORKBOOK_LOAD_WARN_RANGE:
            item = self.build_item_for_web_request(value)
            options.append({'id':value, 'item': item})
        workbook_load_warn['options'] = options

        # workbook error (formerly http load error)
        seconds = req.system[SystemKeys.HTTP_LOAD_ERROR]
        value = self.build_item_for_web_request(seconds)
        workbook_load_error = {'name': SystemKeys.HTTP_LOAD_ERROR,
                               'value': value,
                               'id': seconds}

        options = []
        for value in self.WORKBOOK_LOAD_ERROR_RANGE:
            item = self.build_item_for_web_request(value)
            options.append({'id':value, 'item': item})
        workbook_load_error['options'] = options

        # cpu load warn
        seconds = req.system[SystemKeys.CPU_LOAD_WARN]
        if seconds > 100:
            cpu_load_warn = {'name': SystemKeys.CPU_LOAD_WARN,
                             'value': 'Do not monitor',
                             'id': 101}
        else:
            cpu_load_warn = {'name': SystemKeys.CPU_LOAD_WARN,
                             'value': '%s%%' % str(seconds),
                             'id': seconds}
        options = []
        for value in self.CPU_LOAD_WARN_RANGE:
            if value > 100:
                options.append({'id':value, 'item': "Do not monitor"})
            else:
                options.append({'id':value, 'item': '%s%%' % str(value)})
        cpu_load_warn['options'] = options

        # cpu load error
        seconds = req.system[SystemKeys.CPU_LOAD_ERROR]
        if seconds > 100:
            cpu_load_error = {'name': SystemKeys.CPU_LOAD_ERROR,
                              'value': 'Do not monitor',
                              'id': 101}
        else:
            cpu_load_error = {'name': SystemKeys.CPU_LOAD_ERROR,
                              'value': '%s%%' % str(seconds),
                              'id': seconds}
        options = []
        for value in self.CPU_LOAD_ERROR_RANGE:
            if value > 100:
                options.append({'id':value, 'item': 'Do not monitor'})
            else:
                options.append({'id':value, 'item': '%s%%' % str(value)})
        cpu_load_error['options'] = options

        # cpu period warn
        period_seconds = req.system[SystemKeys.CPU_PERIOD_WARN]

        value = req.system[SystemKeys.CPU_LOAD_WARN]
        if value > 100:
            # not monitoring
            cpu_period_warn = {'name': SystemKeys.CPU_PERIOD_WARN,
                               'value': "Do not Monitor",
                               'id': period_seconds}
        else:
            cpu_period_warn = {'name': SystemKeys.CPU_PERIOD_WARN,
                               'value': (period_seconds / 60),
                               'id': period_seconds}
        options = []
        for value in self.CPU_PERIOD_WARN_RANGE:
            options.append({'id':value * 60, 'item': str(value)})
        cpu_period_warn['options'] = options

        # cpu period error
        period_seconds = req.system[SystemKeys.CPU_PERIOD_ERROR
]
        value = req.system[SystemKeys.CPU_LOAD_ERROR]
        if value > 100:
            # not monitoring
            cpu_period_error = {'name': SystemKeys.CPU_PERIOD_ERROR,
                                'value': "Do not monitor",
                                'id': period_seconds}
        else:
            cpu_period_error = {'name': SystemKeys.CPU_PERIOD_ERROR,
                                'value': str(value / 60),
                                'id': period_seconds}
        options = []
        for value in self.CPU_PERIOD_ERROR_RANGE:
            options.append({'id':value * 60, 'item': str(value)})
        cpu_period_error['options'] = options

        data['config'] = [low, high,
                          workbook_load_warn, workbook_load_error,
                          cpu_load_warn, cpu_load_error,
                          cpu_period_warn, cpu_period_error]

        return data

    @required_role(Role.MANAGER_ADMIN)
    def service_POST(self, req):
        # pylint: disable=unused-argument
        req.system[SystemKeys.WATERMARK_LOW] = req.POST['disk-watermark-low']
        req.system[SystemKeys.WATERMARK_HIGH] = req.POST['disk-watermark-high']

        req.system[SystemKeys.CPU_LOAD_WARN] = req.POST['cpu-load-warn']
        req.system[SystemKeys.CPU_LOAD_ERROR] = req.POST['cpu-load-error']

        req.system[SystemKeys.CPU_PERIOD_WARN] = req.POST['cpu-period-warn']
        req.system[SystemKeys.CPU_PERIOD_ERROR] = req.POST['cpu-period-error']

        req.system[SystemKeys.HTTP_LOAD_WARN] = req.POST['http-load-warn']
        req.system[SystemKeys.HTTP_LOAD_ERROR] = req.POST['http-load-error']

        meta.commit()
        return {}

class _GeneralApplication(PaletteRESTApplication):

    def __init__(self):
        super(_GeneralApplication, self).__init__()
        self.backup = GeneralBackupApplication()
        self.email_alert = EmailAlertApplication()
        self.ziplog = GeneralZiplogApplication()
        self.archive = GeneralArchiveApplication()
        self.storage = _GeneralStorageApplication() # Don't use the Router
        self.monitor = GeneralMonitorApplication()

    @required_role(Role.MANAGER_ADMIN)
    def service_GET(self, req):
        data = {}
        extend(data, self.backup.service_GET(req))
        extend(data, self.email_alert.service_GET(req))
        extend(data, self.ziplog.service_GET(req))
        extend(data, self.archive.service_GET(req))
        extend(data, self.storage.service_GET(req))
        extend(data, self.monitor.service_GET(req))
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
        self.add_route(r'/archive\Z', GeneralArchiveApplication())


class GeneralPage(PalettePage):
    TEMPLATE = "config/general.mako"
    active = 'general'
    expanded = True
    required_role = Role.MANAGER_ADMIN
