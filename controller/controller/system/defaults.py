""" The default values for all possible system table entries.

NOTE: All used keys must be listed here or KeyError is raised when accessed.

The data type is inferred from the value specified. The allowed types are:
  int, bool, str, and dict, with None defaulting to str.

If the default value is a dict, then it may contains the following:
  'value': The default value, defaults to None if not specified.
  'data-type': The type of value, which defaults to 'str'
  'populate': Add a row for this value during setup, defaults to False

"""
# pylint: enable=missing-docstring, relative-import
from .keys import SystemKeys

UNDEFINED_INTEGER = {"value": None, "data-type": int}

UNPOPULATED_TRUE = {"value": True, "populate": False}
UNPOPULATED_FALSE = {"value": False, "populate": False}

HTTP_LOAD_RE = ".+(\\.(xml|png|pdf)(\\Z|\\?)|format=(xml|png|pdf))"

DEFAULTS = {
    SystemKeys.WATERMARK_LOW: 101,
    SystemKeys.WATERMARK_HIGH: 101,

    SystemKeys.STORAGE_ENCRYPT: False,

    SystemKeys.WORKBOOKS_AS_TWB: False,
    SystemKeys.WORKBOOK_LOAD_WARN: 0,
    SystemKeys.WORKBOOK_LOAD_ERROR: 0,
    SystemKeys.WORKBOOK_RETAIN_COUNT: 0,

    SystemKeys.BACKUP_USER_RETAIN_COUNT: 1,
    SystemKeys.BACKUP_AUTO_RETAIN_COUNT: 1,
    SystemKeys.BACKUP_SCHEDULED_PERIOD: 24,
    SystemKeys.BACKUP_SCHEDULED_HOUR: 12,
    SystemKeys.BACKUP_SCHEDULED_MINUTE: '00',
    SystemKeys.BACKUP_SCHEDULED_AMPM: 'AM',
    SystemKeys.BACKUP_SCHEDULED_ENABLED: True,
    SystemKeys.BACKUP_DEST_TYPE: "vol",
    SystemKeys.BACKUP_DEST_ID: UNDEFINED_INTEGER,

    SystemKeys.ZIPLOG_ENABLED: UNPOPULATED_TRUE,
    SystemKeys.ZIPLOG_SCHEDULED_ENABLED: UNPOPULATED_TRUE,
    SystemKeys.ZIPLOG_USER_RETAIN_COUNT: 1,
    SystemKeys.ZIPLOG_AUTO_RETAIN_COUNT: 1,

    SystemKeys.LOG_ARCHIVE_RETAIN_COUNT: 1, #FIXME: needed?

    SystemKeys.ARCHIVE_ENABLED: False,
    SystemKeys.ARCHIVE_SAVE_TWBX: False,

    SystemKeys.HTTP_LOAD_WARN: 0,
    SystemKeys.HTTP_LOAD_ERROR: 0,
    SystemKeys.HTTP_LOAD_RE: HTTP_LOAD_RE,

    SystemKeys.PING_REQUEST_INTERVAL: 10,
    SystemKeys.SOCKET_TIMEOUT: 60,
    SystemKeys.SSL_HANDSHAKE_TIMEOUT: 5,

    SystemKeys.EVENT_DEGRADED_MIN: 30,

    SystemKeys.STATUS_REQUEST_INTERVAL: 30,

    SystemKeys.STATUS_SYSTEMINFO: True,
    SystemKeys.STATUS_SYSTEMINFO_ONLY: False,
    SystemKeys.STATUS_SYSTEMINFO_SEND_ALERTS: False,
    SystemKeys.STATUS_SYSTEMINFO_TIMEOUT_MS: 15000,

    SystemKeys.ALERTS_ENABLED: True,
    SystemKeys.ALERTS_ADMIN_ENABLED: False,
    SystemKeys.ALERTS_PUBLISHER_ENABLED: False,
    SystemKeys.ALERTS_NEW_USER_ENABLED: False,

    SystemKeys.CPU_LOAD_WARN: 101,
    SystemKeys.CPU_LOAD_ERROR: 101,
    SystemKeys.CPU_PERIOD_WARN: 60,
    SystemKeys.CPU_PERIOD_ERROR: 60,

    SystemKeys.METRIC_SAVE_DAYS: 735,
    SystemKeys.MAX_SILENCE_TIME: 72*60*60, # 3 days, use -1 to disable

    SystemKeys.UPGRADING: False,
    SystemKeys.DEBUG_LEVEL: "DEBUG",
    SystemKeys.CONTROLLER_INITIAL_START: UNPOPULATED_FALSE,
    SystemKeys.PALETTE_VERSION: None,

    SystemKeys.AUTHENTICATION_TYPE: 1, # FIXME: AuthType.TABLEAU
    SystemKeys.PALETTE_LOGIN: True,

    SystemKeys.SUPPORT_ENABLED: False,
    SystemKeys.AUTO_UPDATE_ENABLED: False,

    SystemKeys.FROM_EMAIL: "",
    SystemKeys.EMAIL_MAX_COUNT: 10,
    SystemKeys.EMAIL_SPIKE_DISABLED_ALERTS: UNPOPULATED_FALSE,
    SystemKeys.EMAIL_LOOKBACK_MINUTES: 10,

    SystemKeys.MAIL_SERVER_TYPE: 3, # FIXME: MailServerType.DIRECT
    SystemKeys.MAIL_SMTP_SERVER: None,
    SystemKeys.MAIL_SMTP_PORT: UNDEFINED_INTEGER,
    SystemKeys.MAIL_USERNAME: None,
    SystemKeys.MAIL_PASSWORD: None,
    SystemKeys.MAIL_DOMAIN: None,
    SystemKeys.MAIL_ENABLE_TLS: UNPOPULATED_FALSE,

    SystemKeys.SERVER_URL: "https://localhost",
    SystemKeys.TABLEAU_SERVER_URL: None,
    SystemKeys.TABLEAU_INTERNAL_SERVER_URL: None,
    SystemKeys.TIMEZONE: "US/Pacific",
    SystemKeys.PROXY_HTTPS: None,

    SystemKeys.STATE: "DISCONNECTED",

    SystemKeys.S3_ID: UNDEFINED_INTEGER,
    SystemKeys.GCS_ID: UNDEFINED_INTEGER,

    SystemKeys.PLATFORM_PRODUCT: {'value': 'enterprise', 'populate': False},
    SystemKeys.PLATFORM_IMAGE: {'value': 'vmware', 'populate': False},
    SystemKeys.PLATFORM_LOCATION: {'value': 'customer', 'populate': False},

    SystemKeys.AUTH_TIMESTAMP: None,

    SystemKeys.YML_LOCATION: None,
    SystemKeys.YML_TIMESTAMP: None
}

def validate(verbose=False):
    """ Ensure that all SystemKeys constants have corresponding defaults
    Usage within IDLE:
      >>> from controller.system.defaults import validate
      >>> print validate()
    """
    import sys
    result = True
    for name in SystemKeys.__dict__:
        if name.startswith('_'):
            continue
        value = SystemKeys.__dict__[name]
        if not isinstance(value, basestring):
            continue
        if not value in DEFAULTS:
            print >> sys.stderr, "Missing system key : " + name
            result = False
        elif verbose:
            print name + ": OK"
    return result
