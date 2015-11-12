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

from .option import DictOption, TimeOption, PercentOption
from .page import PalettePage
from .rest import required_parameters, required_role, PaletteRESTApplication
from .s3 import S3Application
from .gcs import GCSApplication
from .mixin import CredentialMixin

class BackupZiplogsRetention(DictOption):
    """Representation of the 'Workbook Retention' dropdown."""
    NONE = 0
    ALL = -1

    RETAIN_RANGE = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25]

    def __init__(self, name, valueid):
        options = OrderedDict({})
        options[self.NONE] = 'Disabled'
        for count in self.RETAIN_RANGE:
            options[count] = str(count)
        options[self.ALL] = 'All'
        super(BackupZiplogsRetention, self).__init__(name, valueid, options)

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

    @required_role(Role.READONLY_ADMIN)
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

    @required_role(Role.READONLY_ADMIN)
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
            return {'status': 'FAILED', 'error': err}
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

    @required_role(Role.READONLY_ADMIN)
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

    @required_role(Role.READONLY_ADMIN)
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

    @required_role(Role.READONLY_ADMIN)
    def service_GET(self, req):
        name = SystemKeys.BACKUP_USER_RETAIN_COUNT
        valueid = req.system[name]
        backup_user_retain_opts = BackupZiplogsRetention(name, valueid)

        name = SystemKeys.BACKUP_AUTO_RETAIN_COUNT
        valueid = req.system[name]
        backup_auto_retain_opts = BackupZiplogsRetention(name, valueid)

        data = {}
        data['config'] = [backup_user_retain_opts.default(),
                           backup_auto_retain_opts.default()]
        data['timezone'] = time.strftime("%Z")  # remove?
        return data

    @required_role(Role.MANAGER_ADMIN)
    def service_POST(self, req):
        req.system[SystemKeys.BACKUP_AUTO_RETAIN_COUNT] = \
                                        req.POST['backup-auto-retain-count']
        req.system[SystemKeys.BACKUP_USER_RETAIN_COUNT] = \
                                        req.POST['backup-user-retain-count']
        meta.commit()
        return {}


class EmailAlertApplication(PaletteRESTApplication):
    """Handler for the 'EMAIL ALERTS' section."""

    @required_role(Role.READONLY_ADMIN)
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

    @required_role(Role.READONLY_ADMIN)
    def service_GET(self, req):
        # pylint: disable=unused-argument
        name = SystemKeys.ZIPLOG_USER_RETAIN_COUNT
        valueid = req.system[name]
        ziplog_user_retain_opts = BackupZiplogsRetention(name, valueid)

        name = SystemKeys.ZIPLOG_AUTO_RETAIN_COUNT
        valueid = req.system[name]
        ziplog_auto_retain_opts = BackupZiplogsRetention(name, valueid)

        data = {}
        data['config'] = [ziplog_user_retain_opts.default(),
                           ziplog_auto_retain_opts.default()]
        return data

    @required_role(Role.MANAGER_ADMIN)
    def service_POST(self, req):
        req.system[SystemKeys.ZIPLOG_AUTO_RETAIN_COUNT] = \
                            req.POST['ziplog-auto-retain-count']
        req.system[SystemKeys.ZIPLOG_USER_RETAIN_COUNT] = \
                            req.POST['ziplog-user-retain-count']
        meta.commit()
        return {}

class GeneralArchiveApplication(PaletteRESTApplication, CredentialMixin):
    """Handler for 'ARCHIVE' section - both workbook and datasource settings."""

    @required_role(Role.READONLY_ADMIN)
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

    @required_role(Role.READONLY_ADMIN)
    def service_GET(self, req):
        config = []

        # watermark low
        percent = req.system[SystemKeys.WATERMARK_LOW]
        option = PercentOption(SystemKeys.WATERMARK_LOW, percent,
                               self.LOW_WATERMARK_RANGE)
        config.append(option.default())

        # watermark high
        percent = req.system[SystemKeys.WATERMARK_HIGH]
        option = PercentOption(SystemKeys.WATERMARK_HIGH, percent,
                               self.HIGH_WATERMARK_RANGE)
        config.append(option.default())

        # workbook warn (formerly http load warn)
        seconds = req.system[SystemKeys.HTTP_LOAD_WARN]
        option = TimeOption(SystemKeys.HTTP_LOAD_WARN, seconds,
                            {'seconds': self.WORKBOOK_LOAD_WARN_RANGE})
        config.append(option.default())

        # workbook error (formerly http load error)
        seconds = req.system[SystemKeys.HTTP_LOAD_ERROR]
        option = TimeOption(SystemKeys.HTTP_LOAD_ERROR, seconds,
                            {'seconds': self.WORKBOOK_LOAD_ERROR_RANGE})
        config.append(option.default())

        # cpu load warn
        percent = req.system[SystemKeys.CPU_LOAD_WARN]
        option = PercentOption(SystemKeys.CPU_LOAD_WARN, percent,
                               self.CPU_LOAD_WARN_RANGE)
        config.append(option.default())

        # cpu load error
        percent = req.system[SystemKeys.CPU_LOAD_ERROR]
        option = PercentOption(SystemKeys.CPU_LOAD_ERROR, percent,
                               self.CPU_LOAD_ERROR_RANGE)
        config.append(option.default())

        # cpu period warn
        seconds = req.system[SystemKeys.CPU_PERIOD_WARN]
        option = TimeOption(SystemKeys.CPU_PERIOD_WARN, seconds,
                            {'minutes': self.CPU_PERIOD_WARN_RANGE})
        config.append(option.default())

        # cpu period error
        seconds = req.system[SystemKeys.CPU_PERIOD_ERROR]
        option = TimeOption(SystemKeys.CPU_PERIOD_ERROR, seconds,
                            {'minutes': self.CPU_PERIOD_ERROR_RANGE})
        config.append(option.default())

        return {'config': config}

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

class GeneralExtractApplication(PaletteRESTApplication):
    """ The Extracts section of the General configuration page. """

    DELAY_RANGE = {'minutes': (10, 30),
                   'hours': (1, 2, 3, 4, 5, 6, 12, 24)}
    DURATION_RANGE = {'minutes': (5, 10, 15, 30, 60)}

    @required_role(Role.READONLY_ADMIN)
    def service_GET(self, req):
        config = []
        for key in (SystemKeys.EXTRACT_DELAY_WARN,
                    SystemKeys.EXTRACT_DELAY_ERROR):
            option = TimeOption(key, req.system[key], self.DELAY_RANGE)
            config.append(option.default())
        for key in (SystemKeys.EXTRACT_DURATION_WARN,
                    SystemKeys.EXTRACT_DURATION_ERROR):
            option = TimeOption(key, req.system[key], self.DURATION_RANGE)
            config.append(option.default())
        return {'config': config}


class _GeneralApplication(PaletteRESTApplication):

    def __init__(self):
        super(_GeneralApplication, self).__init__()
        self.backup = GeneralBackupApplication()
        self.email_alert = EmailAlertApplication()
        self.ziplog = GeneralZiplogApplication()
        self.archive = GeneralArchiveApplication()
        self.storage = _GeneralStorageApplication() # Don't use the Router
        self.monitor = GeneralMonitorApplication()
        self.extract = GeneralExtractApplication()

    @required_role(Role.READONLY_ADMIN)
    def service_GET(self, req):
        data = {}
        extend(data, self.backup.service_GET(req))
        extend(data, self.email_alert.service_GET(req))
        extend(data, self.ziplog.service_GET(req))
        extend(data, self.archive.service_GET(req))
        extend(data, self.storage.service_GET(req))
        extend(data, self.monitor.service_GET(req))
        extend(data, self.extract.service_GET(req))
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
        self.add_route(r'/extract\Z', GeneralExtractApplication())


class GeneralPage(PalettePage):
    TEMPLATE = "config/general.mako"
    active = 'general'
    expanded = True
    required_role = Role.MANAGER_ADMIN
