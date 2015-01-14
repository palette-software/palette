from files import FileManager
import logging
from cloud import S3_ID, GCS_ID

# This a transitory class - instantiated each time it is needed.
class SystemConfig(object):
    # Keys for the system table:
    STORAGE_ENCRYPT = "storage-encrypt"       # "yes" or "no"
    BACKUP_AUTO_RETAIN_COUNT = "backup-auto-retain-count"
    BACKUP_USER_RETAIN_COUNT = "backup-user-retain-count"
    BACKUP_DEST_TYPE = "backup-dest-type"   # "vol" or "cloud"
    BACKUP_DEST_ID = "backup-dest-id"
    LOG_ARCHIVE_RETAIN_COUNT = "log-archive-retain-count"
    WORKBOOKS_AS_TWB = "workbooks-as-twb"

    WATERMARK_LOW = "disk-watermark-low"
    WATERMARK_HIGH = "disk-watermark-high"

    HTTP_LOAD_WARN = "http-load-warn"
    HTTP_LOAD_ERROR = "http-load-error"

    CPU_LOAD_WARN = "cpu-load-warn"
    CPU_LOAD_ERROR = "cpu-load-error"
    CPU_PERIOD_WARN = "cpu-period-warn"
    CPU_PERIOD_ERROR = "cpu-period-error"
    METRIC_SAVE_DAYS = 'metric-save-days'

    ALERTS_ENABLED = "alerts-enabled"
    ALERTS_ADMIN_ENABLED = 'alerts-admin-enabled'
    ALERTS_PUBLISHER_ENABLED = 'alerts-publisher-enabled'

    PALETTE_VERSION = "palette-version"

    UPGRADING = "upgrading"

    DEBUG_LEVEL = 'debug-level'
    FROM_EMAIL = 'from-email'

    # Don't take 'server' here so that this class may be instantiated
    # from the webapp too.
    def __init__(self, system):
        self.system = system
        # NOTE: All values a read from the system table as needed
        # using the __getattr__ mechanism

        # FIXME: add a 'populate' keyword option that reads the entire table.

    def _getyesno(self, name, **kwargs):
        value = self.system.get(name, **kwargs).lower()
        if value == 'no':
            return False
        elif value == 'yes':
            return True
        else:
            raise ValueError("Bad value for system '%s': '%s'" % (name, value))

    def _getint(self, name, **kwargs):
        value = self.system.get(name, **kwargs)
        return int(value) # Throws exception if non-digit.

    def _getstring(self, name, **kwargs):
        return self.system.get(name, **kwargs)

    def _backup_dest_type(self):
        value = self.system.get(self.BACKUP_DEST_TYPE,
                                 default=FileManager.STORAGE_TYPE_VOL)
        if value not in (FileManager.STORAGE_TYPE_VOL,
                         FileManager.STORAGE_TYPE_CLOUD):
            raise ValueError("system '%s' not yet set or corrupted: '%s'." % \
                                 (self.BACKUP_DEST_TYPE, value))
        return value

    def _watermark(self, name):
        try:
            return int(self.system.get(name))
        except StandardError:
            return 100

    def _http_load_warn(self, name):
        try:
            return int(self.system.get(name))
        except StandardError:
            return 10

    def _http_load_error(self, name):
        try:
            return int(self.system.get(name))
        except StandardError:
            return 20

    def _debug_level(self, name, **kwargs):
        """Returns an integer level, based on the logging level string."""
        level_str = self.system.get(name, **kwargs)

        level_str = level_str.upper().strip()
        if level_str not in ('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'):
            level_str = 'DEBUG'

        return getattr(logging, level_str)

    def __getattr__(self, name):
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches
        if name == 'watermark_low':
            return self._watermark(self.WATERMARK_LOW)
        if name == 'watermark_high':
            return self._watermark(self.WATERMARK_HIGH)
        if name == 'backup_dest_id':
            return self._getint(self.BACKUP_DEST_ID, default=-1)
        if name == 'backup_dest_type':
            return self._backup_dest_type()
        if name == 'log_archive_retain_count':
            return self._getint(self.LOG_ARCHIVE_RETAIN_COUNT)
        if name == 'backup_user_retain_count':
            return self._getint(self.BACKUP_USER_RETAIN_COUNT)
        if name == 'backup_auto_retain_count':
            return self._getint(self.BACKUP_AUTO_RETAIN_COUNT)
        if name == 'storage_encrypt':
            return self._getyesno(self.STORAGE_ENCRYPT)
        if name == 'workbooks_as_twb':
            return self._getyesno(self.WORKBOOKS_AS_TWB)
        if name == 'http_load_warn':
            return self._http_load_warn(self.HTTP_LOAD_WARN)
        if name == 'http_load_error':
            return self._http_load_error(self.HTTP_LOAD_ERROR)
        if name == 'alerts_enabled':
            return self._getyesno(self.ALERTS_ENABLED)
        if name == 'alerts_admin_enabled':
            return self._getyesno(self.ALERTS_ADMIN_ENABLED)
        if name == 'alerts_publisher_enabled':
            return self._getyesno(self.ALERTS_PUBLISHER_ENABLED)
        if name == 'upgrading':
            return self._getyesno(self.UPGRADING)
        if name == 'cpu_load_warn':
            return self._getint(self.CPU_LOAD_WARN, default=80)
        if name == 'cpu_load_error':
            return self._getint(self.CPU_LOAD_ERROR, default=95)
        if name == 'cpu_period_warn':
            return self._getint(self.CPU_PERIOD_WARN, default=60)
        if name == 'cpu_period_error':
            return self._getint(self.CPU_PERIOD_ERROR, default=60)
        if name == 'metric_save_days':
            return self._getint(self.METRIC_SAVE_DAYS, default=1)
        if name == 'debug_level':
            return self._debug_level(self.DEBUG_LEVEL, default='DEBUG')
        if name == 's3_id':
            return self._getint(S3_ID, default=0)
        if name == 'gcs_id':
            return self._getint(GCS_ID, default=0)
        if name == 'from_email':
            return self._getstring(self.FROM_EMAIL,
                        default="Palette Alerts <alerts@palette-software.com>")
        raise AttributeError(name)

    def todict(self):
        return {
            self.STORAGE_ENCRYPT: self.storage_encrypt,
            self.BACKUP_AUTO_RETAIN_COUNT: self.backup_auto_retain_count,
            self.BACKUP_USER_RETAIN_COUNT: self.backup_user_retain_count,
            self.BACKUP_DEST_TYPE: self.backup_dest_type,
            self.BACKUP_DEST_ID: self.backup_dest_id,
            self.WATERMARK_LOW: self.watermark_low,
            self.WATERMARK_HIGH: self.watermark_high,
            self.LOG_ARCHIVE_RETAIN_COUNT: self.log_archive_retain_count,
            self.HTTP_LOAD_WARN: self.http_load_warn,
            self.HTTP_LOAD_ERROR: self.http_load_error,
            self.ALERTS_ENABLED: self.alerts_enabled,
            self.ALERTS_ADMIN_ENABLED: self.alerts_admin_enabled,
            self.ALERTS_PUBLISHER_ENABLED: self.alerts_publisher_enabled,
            self.PALETTE_VERSION: self.palette_version,
            self.UPGRADING: self.upgrading,
            self.CPU_LOAD_WARN: self.cpu_load_warn,
            self.CPU_LOAD_ERROR: self.cpu_load_error,
            self.CPU_PERIOD_WARN: self.cpu_load_warn,
            self.CPU_PERIOD_ERROR: self.cpu_period_error,
            self.METRIC_SAVE_DAYS: self.metric_save_days,
            self.DEBUG_LEVEL: self.debug_level,
            self.FROM_EMAIL: self.from_email
            }

    def text(self, value):
        if ':' in value:
            tokens = value.split(':')
            value = tokens[0]
        if value == FileManager.STORAGE_TYPE_VOL:
            return 'Agent Volume'
        if value == FileManager.STORAGE_TYPE_CLOUD:
            return 'Cloud Storage'
        raise KeyError(value)
