from files import FileManager

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

    ALERTS_ENABLED = "alerts-enabled"

    PALETTE_VERSION = "palette-version"

    UPGRADING = "upgrading"

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
        if name == 'upgrading':
            return self._getyesno(self.UPGRADING)

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
            self.PALETTE_VERSION: self.palette_version,
            self.UPGRADING: self.upgrading,
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
