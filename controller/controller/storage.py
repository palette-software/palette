# This a transitory class - instantiated each time it is needed.
class StorageConfig(object):
    # Keys for the system table:
    STORAGE_ENCRYPT="storage-encrypt"       # "yes" or "no"
    BACKUP_AUTO_RETAIN_COUNT="backup-auto-retain-count"
    BACKUP_USER_RETAIN_COUNT="backup-user-retain-count"
    BACKUP_DEST_TYPE="backup-dest-type"   # "vol", "gcs" or "s3"
    BACKUP_DEST_ID="backup-dest-id"

    VOL="vol"
    GCS="gcs"
    S3="s3"

    def __init__(self, server):
        self.system = server.system

        encrypt = self.system.get(self.STORAGE_ENCRYPT)
        if not encrypt or encrypt == 'no':
            self.storage_encrypt = False
        elif encrypt == 'yes':
            self.storage_encrypt = True
        else:
            raise ValueError("Bad value for system '%s': '%s" % (\
                                    self.STORAGE_ENCRYPT, encrypt))

        auto_retain_count = self.system.get(self.BACKUP_AUTO_RETAIN_COUNT)
        if not auto_retain_count.isdigit():
            raise ValueError("Bad value for system '%s': '%s" %
                            (self.BACKUP_AUTO_RETAIN_COUNT, auto_retain_count))
        self.backup_auto_retain_count = int(auto_retain_count)

        user_retain_count = self.system.get(self.BACKUP_USER_RETAIN_COUNT)
        if not user_retain_count.isdigit():
            raise ValueError("Bad value for system '%s': '%s" % \
                            (self.BACKUP_USER_RETAIN_COUNT, user_retain_count))

        self.backup_user_retain_count = int(auto_retain_count)

        self.backup_dest_type = self.system.get(self.BACKUP_DEST_TYPE)
        if not self.backup_dest_type or \
                    self.backup_dest_type not in (self.VOL, self.GCS, self.S3):
            raise ValueError("system '%s' not yet set or corrupted: '%s'." % \
                            (self.BACKUP_DEST_TYPE, self.backup_dest_type))

        backup_dest_id = self.system.get(self.BACKUP_DEST_ID)
        if not backup_dest_id.isdigit():
            raise ValueError("Bad value for system '%s': '%s" % \
                                    (self.BACKUP_DEST_ID, backup_dest_id))

        self.backup_dest_id = int(backup_dest_id)
