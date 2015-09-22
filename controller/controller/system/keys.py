""" The complete list of allowable system table keys
NOTE: when a new key is added here, that key *must* also be added to DEFAULTS.
"""

class SystemKeys(object):
    """ Keys for the system table.  The purpose of having this class is so
    that pylint can catch bad values which it can't do with bare strings. """
    STORAGE_ENCRYPT = 'storage-encrypt'       # "yes" or "no"
    BACKUP_AUTO_RETAIN_COUNT = 'backup-auto-retain-count'
    BACKUP_USER_RETAIN_COUNT = 'backup-user-retain-count'
    BACKUP_DEST_TYPE = 'backup-dest-type'   # "vol" or "cloud"
    BACKUP_DEST_ID = 'backup-dest-id'

    BACKUP_SCHEDULED_PERIOD = 'backup-scheduled-period'
    BACKUP_SCHEDULED_HOUR = 'backup-scheduled-hour'
    BACKUP_SCHEDULED_MINUTE = 'backup-scheduled-minute'
    BACKUP_SCHEDULED_AMPM = 'backup-scheuled-ampm'
    BACKUP_SCHEDULED_ENABLED = 'backup-scheduled-enabled'

    ZIPLOG_AUTO_RETAIN_COUNT = 'ziplog-auto-retain-count'
    ZIPLOG_USER_RETAIN_COUNT = 'ziplog-user-retain-count'
    ZIPLOG_ENABLED = 'ziplog-enabled'
    ZIPLOG_SCHEDULED_ENABLED = 'ziplog-scheduled-enabled'

    ARCHIVE_SAVE_TWBX = 'archive-save-twbx'
    WORKBOOKS_AS_TWB = 'workbooks-as-twb'

    WORKBOOK_ARCHIVE_ENABLED = 'workbook-archive-enabled'
    WORKBOOK_RETAIN_COUNT = 'workbook-retain-count'
    WORKBOOK_LOAD_WARN = 'workbook-load-warn'
    WORKBOOK_LOAD_ERROR = 'workbook-load-error'

    DATASOURCE_ARCHIVE_ENABLED = 'datasource-archive-enabled'
    DATASOURCE_RETAIN_COUNT = 'datasource-retain-count'
    DATASOURCE_SAVE_TDSX = 'datasource-save-tdsx'

    LOG_ARCHIVE_RETAIN_COUNT = 'log-archive-retain-count'

    WATERMARK_LOW = 'disk-watermark-low'
    WATERMARK_HIGH = 'disk-watermark-high'

    HTTP_LOAD_WARN = 'http-load-warn'
    HTTP_LOAD_ERROR = 'http-load-error'
    HTTP_LOAD_RE = 'http-load-re'

    CPU_LOAD_WARN = 'cpu-load-warn'
    CPU_LOAD_ERROR = 'cpu-load-error'
    CPU_PERIOD_WARN = 'cpu-period-warn'
    CPU_PERIOD_ERROR = 'cpu-period-error'
    METRIC_SAVE_DAYS = 'metric-save-days'

    ALERTS_ENABLED = 'alerts-enabled'
    ALERTS_ADMIN_ENABLED = 'alerts-admin-enabled'
    ALERTS_PUBLISHER_ENABLED = 'alerts-publisher-enabled'
    ALERTS_NEW_USER_ENABLED = 'alerts-new-user-enabled'

    EMAIL_LOOKBACK_MINUTES = 'email-lookback-minutes'
    EMAIL_MAX_COUNT = 'email-max-count'
    EMAIL_SPIKE_DISABLED_ALERTS = 'email-spike-disabled-alerts'

    PALETTE_VERSION = 'palette-version'
    PALETTE_LOGIN = 'palette-login'

    UPGRADING = 'upgrading'
    STATE = 'state'

    DEBUG_LEVEL = 'debug-level'
    FROM_EMAIL = 'from-email'

    # EVENT_SUMMARY_FORMAT = 'event-summary-format'
    EVENT_DEGRADED_MIN = 'event-degraded-min'

    MAIL_SERVER_TYPE = 'mail-server-type'
    MAIL_DOMAIN = 'mail-domain'
    MAIL_ENABLE_TLS = 'mail-enable-tls'
    MAIL_SMTP_SERVER = 'mail-smtp-server'
    MAIL_SMTP_PORT = 'mail-smtp-port'
    MAIL_USERNAME = 'mail-username'
    MAIL_PASSWORD = 'mail-password'

    SERVER_URL = 'server-url'
    TABLEAU_SERVER_URL = 'tableau-server-url'
    TABLEAU_INTERNAL_SERVER_URL = 'tableau-internal-server-url'
    AUTHENTICATION_TYPE = 'authentication-type'

    SOCKET_TIMEOUT = 'socket-timeout'
    PING_REQUEST_INTERVAL = 'ping-request-interval'
    SSL_HANDSHAKE_TIMEOUT = 'ssl-handshake-timeout'

    TIMEZONE = 'timezone'

    CONTROLLER_INITIAL_START = 'controller-initial-start'

    STATUS_REQUEST_INTERVAL = 'status-request-interval'

    STATUS_SYSTEMINFO = 'status-systeminfo'
    STATUS_SYSTEMINFO_ONLY = 'status-systeminfo-only'
    STATUS_SYSTEMINFO_SEND_ALERTS = 'status-systeminfo-send-alerts'
    STATUS_SYSTEMINFO_TIMEOUT_MS = 'status-systeminfo-timeout-ms'

    PROXY_HTTPS = 'proxy-https'
    MAX_SILENCE_TIME = 'max-silence-time'

    SUPPORT_ENABLED = 'support-enabled'
    AUTO_UPDATE_ENABLED = 'auto-update-enabled'

    S3_ID = 's3-id'
    GCS_ID = 'gcs-id'

    PLATFORM_PRODUCT = 'platform-product'
    PLATFORM_IMAGE = 'platform-image'
    PLATFORM_LOCATION = 'platform-location'

    AUTH_TIMESTAMP = 'auth-timestamp'

    YML_TIMESTAMP = 'yml-timestamp'
    YML_LOCATION = 'yml-location'
