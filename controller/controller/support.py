"""
Module for creating a support case for Tableau.
The only interface to this module should be the 'support_case' function.
"""
# pylint: enable=relative-import,missing-docstring
from __future__ import absolute_import

import logging
import os
import binascii
from datetime import datetime, timedelta

from .cloud import CloudInfo
from .event_control import EventControl
from .system import SystemKeys
from .util import failed, status_ok, status_failed

SUPPORT_DATEFMT = '%m/%d/%Y'

logger = logging.getLogger()

# fixme: copied from (broken) akiri.framework
# from akiri.framework.util import generate_token
def generate_token(length=16):
    """Generate a random token of a specified length."""
    return binascii.hexlify(os.urandom(length))

def support_date():
    """Return the 'from' date - i.e. two days ago - for the request."""
    date = datetime.now() - timedelta(days=2)
    return date.strftime(SUPPORT_DATEFMT)

def support_ziplogs(server, agent, volume_entry, filename=None):
    """Run the prescribed ziplogs command and return the path on success."""
    if filename:
        if not filename.lower().endswith('.zip'):
            filename = filename + '.zip'
    else:
        filename = generate_token() + '.zip'
    path = agent.path.join(volume_entry.full_path(), filename)
    date = support_date()
    cmd = 'tabadmin ziplogs -f -l -n -d %s \\\"%s\\\"' % (date, path)
    data = server.cli_cmd(cmd, agent, timeout=60*60)
    data['filename'] = filename
    data['path'] = path
    return data

def support_failed(server, agent, data, userid=None):
    """Generate a ZIPLOGS_FAILED event and return.
    The output of this call should be ok to send back to the user as the
    response to an API call.
    """
    server.event_control.gen(EventControl.ZIPLOGS_FAILED,
                             dict(data.items() + agent.todict().items()),
                             userid=userid)
    result = status_failed(data['error'])
    for key in ('filename', 'path', 'url'):
        if key in data:
            result[unicode(key)] = unicode(data[key])
    return result

def support_case(server, agent, userid=None, filename=None):
    """
    Builds a support case and uploads it to anonymous S3.
    NOTES:
     - The first argument is the controller instance.
     - There must be ~100MB of available space (arbitrary guess...).
    """
    volume_entry = agent.find_space(100*1024*1024)
    if not volume_entry:
        data = status_failed("Insufficent space available: 100MB required.")
        return support_failed(server, agent, data, userid=userid)

    logger.debug("Support case will use '%s'", volume_entry.full_path)

    data = support_ziplogs(server, agent, volume_entry, filename=filename)
    if failed(data):
        return support_failed(server, agent, data, userid=userid)

    filename = data['filename']
    path = data['path']
    logger.debug("Generated ziplog '%s' for support case.", path)

    cloud_info = CloudInfo(server.cloud.CLOUD_TYPE_S3, '/' + filename)
    cloud_info.bucket = server.system[SystemKeys.SUPPORT_CASE_BUCKET]
    cloud_info.access_key = server.system[SystemKeys.ANONYMOUS_ACCESS_KEY]
    cloud_info.secret_key = server.system[SystemKeys.ANONYMOUS_SECRET_KEY]

    logger.debug("Sending support case to S3 bucket '%s'.", cloud_info.bucket)

    data = server.cloud.s3.send_put(agent, cloud_info, path)
    agent.filemanager.delete(path)

    if failed(data):
        return support_failed(server, agent, data, userid=userid)

    result = status_ok()
    result[u'filename'] = unicode(filename)
    result[u'url'] = unicode(cloud_info.external_url())
    if 'size' in data:
        result[u'size'] = data['size']

    logger.debug("Support case is available at '%s'", result['url'])
    return result
