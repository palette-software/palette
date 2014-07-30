# This a transitory class - instantiated each time it is needed.
class StorageConfig(object):
    # Keys for the system table:
    STORAGE_ENCRYPT="storage-encrypt"       # "yes" or "no"
    BACKUP_AUTO_RETAIN_COUNT="backup-auto-retain-count"
    BACKUP_USER_RETAIN_COUNT="backup-user-retain-count"
    BACKUP_DEST_TYPE="backup-dest-type"   # "vol", "gcs" or "s3"
    BACKUP_DEST_ID="backup-dest-id"
    LOG_ARCHIVE_RETAIN_COUNT="log-archive-retain-count"
    WORKBOOKS_AS_TWB="workbooks-as-twb"

    WATERMARK_LOW = "disk-watermark-low"
    WATERMARK_HIGH = "disk-watermark-high"

    VOL="vol"
    GCS="gcs"
    S3="s3"

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
        value =  self.system.get(self.BACKUP_DEST_TYPE, default=self.VOL)
        if value not in (self.VOL, self.GCS, self.S3):
            raise ValueError("system '%s' not yet set or corrupted: '%s'." % \
                                 (self.BACKUP_DEST_TYPE, value))
        return value

    def _watermark(self, name):
        try:
            return int(self.system.get(name))
        except:
            return 100

    def __getattr__(self, name):
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

    def todict(self):
        return {
            self.STORAGE_ENCRYPT: self.storage_encrypt,
            self.BACKUP_AUTO_RETAIN_COUNT: self.backup_auto_retain_count,
            self.BACKUP_USER_RETAIN_COUNT: self.backup_user_retain_count,
            self.BACKUP_DEST_TYPE: self.backup_dest_type,
            self.BACKUP_DEST_ID: self.backup_dest_id,
            self.WATERMARK_LOW: self.watermark_low,
            self.WATERMARK_HIGH: self.watermark_high,
            self.LOG_ARCHIVE_RETAIN_COUNT: self.log_archive_retain_count
            }

    def text(self, value):
        if ':' in value:
            tokens = value.split(':')
            value = tokens[0]
        if value == StorageConfig.VOL:
            return 'Local Volume'
        if value == StorageConfig.S3:
            return 'Amazon S3 Storage'
        if value == StorageConfig.GCS:
            return 'Google Cloud Storage'
        raise KeyError(value)
