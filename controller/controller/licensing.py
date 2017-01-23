# This module is named licensing to avoid the Python reserved keyword 'license'.

import logging
import urllib
import urllib2
from urlparse import urlparse
import httplib
import json
import re
import datetime
import subprocess

from sqlalchemy import Column, Integer, BigInteger, DateTime, Boolean, String
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.schema import ForeignKey

import akiri.framework.sqlalchemy as meta

from event_control import EventControl
from manager import Manager
from mixin import BaseMixin, BaseDictMixin
from util import version, seconds_since

from agent import Agent
from agentmanager import AgentManager
from domain import Domain
from system import SystemKeys
from yml import YmlEntry


LICENSING_URL = "https://licensing.palette-software.com"

def licensing_urlopen(path_info, system, data=None):
    """ Call urllib2.urlopen but with proxy settings (if applicable)
    GET request if data=None, POST otherwise.  data is a dict().
    Raises: urllib2.HTTPError
    """
    proxy_https = system[SystemKeys.PROXY_HTTPS]
    if proxy_https:
        result = urlparse(proxy_https)
        proxy = urllib2.ProxyHandler({'https': result.netloc})
        opener = urllib2.build_opener(proxy)
        urlopen = opener.open
    else:
        urlopen = urllib2.urlopen

    # NOTE: don't install the opener, just use it directly otherwise removing
    # the proxy-https doesn't work.

    if data is None:
        params = None
    else:
        params = urllib.urlencode(data)

    return urlopen(LICENSING_URL + path_info, params)


def licensing_send(path_info, data, system):
    """ Decides whether licensing server is really contacted"""

    # Licensing is disabled
    # return real_licensing_send(path_info, data, system)

    return fake_licensing_send()


def fake_licensing_send():
    """ Always returns valid license """

    data = { # 'id': entry.id,
            'trial': False,
             # 'stage': Stage.get_by_id(entry.stageid).name,
             # 'name': entry.name,
            'expiration-time': datetime.datetime.now() + datetime.timedelta(days=365) }

    return data


def real_licensing_send(path_info, data, system):
    """ Send a POST request to licensing """
    try:
        conn = licensing_urlopen(path_info, system, data=data)
    except urllib2.HTTPError, err:
        status_code = err.code
        reply_json = ""
    else:

        status_code = conn.getcode()
        reply_json = conn.read()
        conn.close()

    if status_code != httplib.OK:
        logging.warn("phone home failed with status %d: '%s'",
                     status_code, reply_json)
        raise LicenseException(status_code,
                               "Failed with status %d. Reply: '%s' " % \
                               (status_code, reply_json))

    return json.loads(reply_json)

def licensing_hello(system):
    """Call /hello on licensing.
    This call is used to check connectivity e.g. from the initial setup page.

    Returns: the status code (200 == success)
    """
    try:
        conn = licensing_urlopen('/hello', system)
        status_code = conn.getcode()
        conn.close()
    except urllib2.HTTPError, err:
        status_code = err.code
    except (httplib.HTTPException, urllib2.URLError):
        # both httplib.BadStatusLine and urllib2.URLError are possible
        status_code = None

    return status_code

def licensing_info(domain, envid, system):
    """Don't do anything very active since this can run when
    in UPGRADE state, etc."""

    data = {}
    data['license-key'] = domain.license_key
    data['system-id'] = domain.systemid
    data['expiration-time'] = domain.expiration_time
    data['contact-time'] = domain.contact_time
    data['trial'] = domain.trial

    data['platform-product'] = system[SystemKeys.PLATFORM_PRODUCT]
    data['platform-image'] = system[SystemKeys.PLATFORM_IMAGE]
    data['platform-location'] = system[SystemKeys.PLATFORM_LOCATION]

    data['auto-update-enabled'] = system[SystemKeys.AUTO_UPDATE_ENABLED]
    data['support-enabled'] = system[SystemKeys.SUPPORT_ENABLED]

    # FIXME: use the version() function when sorted out.
    data['palette-version'] = version()

    data['repo'] = _repo()

    try:
        agent = meta.Session.query(Agent).\
                filter(Agent.agent_type == AgentManager.AGENT_TYPE_PRIMARY).\
                one()
    except NoResultFound:
        #            print "No primary agents ever connected."
        return data

    entry = LicenseEntry.get_by_agentid(agent.agentid)
    if not entry:
        logging.debug("No tableau license entry yet.")
        return data

    data['license-type'] = entry.license_type

    if entry.license_type == LicenseEntry.LICENSE_TYPE_NAMED_USER:
        data['license-quantity'] = entry.interactors
    elif entry.license_type == LicenseEntry.LICENSE_TYPE_CORE:
        data['license-quantity'] = entry.cores  # used
        data['license-core-licenses'] = entry.core_licenses  # available/bought
    else:
        data['license-quantity'] = None

    data['tableau-version'] = YmlEntry.get(envid, 'version.external',
                                           default='unknown')

    data['tableau-bitness'] = YmlEntry.get(envid, 'version.bitness',
                                           default='unknown')

    data['processor-type'] = agent.processor_type
    data['processor-count'] = agent.processor_count
    data['processor-bitness'] = agent.bitness
    data['primary-uuid'] = agent.uuid
    data['primary-os-version'] = agent.os_version

    agents = meta.Session.query(Agent).\
                all()

    agent_info = []
    for agent in agents:
        agent_info.append({'displayname': agent.displayname,
                           'hostname': agent.hostname,
                           'type': agent.agent_type,
                           'version': agent.version})

    data['agent-info'] = agent_info
    return data

REPO = None

def _repo():
    # pylint: disable=global-statement
    global REPO

    if REPO:
        # Used the cached version
        return REPO

    cmd = "apt-cache madison controller | awk '{ print $5 }' 2>/dev/null"
    try:
        REPO = subprocess.check_output(cmd, shell=True).strip()
    except subprocess.CalledProcessError:
        return 'UNKNOWN'

    REPO = urlparse(REPO).path.strip('/')
    return REPO

class LicenseException(StandardError):
    def __init__(self, status, reason):
        message = str(status) + ' ' + reason
        StandardError.__init__(self, message)
        self.status = status
        self.reason = reason

class LicenseEntry(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = 'license'

    LICENSE_TYPE_NAMED_USER = "Named-user"
    LICENSE_TYPE_CORE = "Core"

    licenseid = Column(BigInteger, primary_key=True)
    agentid = Column(BigInteger,
                    ForeignKey("agent.agentid", ondelete='CASCADE'),
                     nullable=False, unique=True)
    interactors = Column(Integer)
    viewers = Column(Integer)
    cores = Column(Integer)
    core_licenses = Column(Integer)
    license_type = Column(String)
    notified = Column(Boolean, nullable=False, default=False) # deprecated
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(),
                               onupdate=func.current_timestamp())

    @classmethod
    def get_by_agentid(cls, agentid):
        try:
            entry = meta.Session.query(LicenseEntry).\
                filter(LicenseEntry.agentid == agentid).\
                one()
        except NoResultFound:
            return None
        return entry

    @classmethod
    def get(cls, agentid, **kwargs):
        session = meta.Session()
        entry = cls.get_by_agentid(agentid)
        if not entry:
            entry = LicenseEntry(agentid=agentid)
            session.add(entry)

        if 'interactors' in kwargs and kwargs['interactors'].isdigit():
            entry.license_type = LicenseEntry.LICENSE_TYPE_NAMED_USER
            entry.interactors = int(kwargs['interactors'])
            if 'viewers' in kwargs and kwargs['viewers'].isdigit():
                entry.viewers = int(kwargs['viewers'])
            entry.cores = 0
            entry.core_licenses = 0
            return entry
        elif 'cores' in kwargs:
            entry.license_type = LicenseEntry.LICENSE_TYPE_CORE
            entry.cores = kwargs['cores']
            entry.core_licenses = kwargs['core-licenses']
            entry.interactors = 0
            entry.viewers = 0
            return entry

        # Default setting to let us know the license info has been
        # received. It could be 0 interactors and 0 viewers, which
        # means "no license".
        entry.license_type = LicenseEntry.LICENSE_TYPE_NAMED_USER
        entry.cores = 0
        entry.core_licenses = 0

        return entry

    @classmethod
    def all(cls):
        return cls.get_all_by_keys({})

    @classmethod
    def parse(cls, output):
        # pylint: disable=anomalous-backslash-in-string
        pattern = '(?P<interactors>\d+) interactors, (?P<viewers>\d+) viewers'
        match = re.search(pattern, output)
        if match:
            return match.groupdict()

        if output.find("Cores used") == -1:
            print "Unknown format for license report:", output
            return {}

        for line in output.splitlines():
            if line.find("Cores used") == -1:
                continue
            try:
                cores = int(line.split()[-3])
                core_licenses = int(line.split()[-1])
            except (IndexError, ValueError):
                print "Invalid format for cores license report:", line
                return {}
            return {'cores': cores, 'core-licenses': core_licenses}
        print "Unexpected failure for license check."
        return {}

    def gettype(self):
        return str(self.license_type)

    def valid(self):
        # pylint: disable=too-many-return-statements
        if self.license_type == LicenseEntry.LICENSE_TYPE_CORE:
            if self.cores:
                return True
            else:
                return False
        elif self.license_type == LicenseEntry.LICENSE_TYPE_NAMED_USER:
            if self.interactors or self.viewers:
                return True
            else:
                return False
        elif self.license_type is None:
            # License hasn't been retrieved yet: OK unless proved otherwise.
            return True

        if self.interactors is None and self.viewers is None and \
                                                        self.cores is None:
            # License hasn't been retrieved yet: OK unless proved otherwise.
            return True

        return False

    def invalid(self):
        return not self.valid()

    def capacity(self):
        if self.cores:
            return "Cores used: %d of %d" % (self.cores, self.core_licenses)
        if self.interactors is None and self.viewers is None:
            return None
        return "%d Interactors, %d Viewers" % (self.interactors, self.viewers)


class LicenseManager(Manager):
    def check(self, agent):
        server = self.server

        body = server.cli_cmd('tabadmin license', agent, timeout=60*10)

        if not 'exit-status' in body or body['exit-status'] != 0:
            return body
        if not 'stdout' in body:
            return body

        session = meta.Session()
        output = body['stdout']
        license_data = LicenseEntry.parse(output)
        entry = LicenseEntry.get(agentid=agent.agentid, **license_data)
        session.commit()

        msg = "License type: %s, " % str(entry.license_type)
        if entry.license_type == LicenseEntry.LICENSE_TYPE_NAMED_USER:
            msg += "interactors: %s, viewers: %s" % \
                        (str(entry.interactors), str(entry.viewers))
        elif entry.license_type == LicenseEntry.LICENSE_TYPE_CORE:
            msg += "cores used: %s of %s" % \
                    (str(entry.cores), str(entry.core_licenses))
        else:
            msg += "interactors: %s, viewers: %s, cores used: %s of %s" \
                        % (str(entry.interactors), str(entry.viewers),
                           str(entry.cores), str(entry.core_licenses))

        notification = self.server.notifications.get("tlicense")

        if entry.valid():
            if notification.color == 'red':
                data = agent.todict()
                data['stdout'] = msg
                self.server.event_control.gen(EventControl.LICENSE_VALID, data)
                # Remember when we sent the notification
                notification.modification_time = func.now()
                notification.color = 'green'
                notification.notified_color = 'green'
                notification.description = None
                session.commit()
            return license_data
        else:
            # license is invalid
            if notification.color != 'red':
                # Generate an event
                data = agent.todict()
                data['error'] = msg
                if notification.color != 'red':
                    self.server.event_control.gen(EventControl.LICENSE_INVALID,
                                                  data)

                notification.color = 'red'
                notification.notified_color = 'red'
                # Remember when we sent the notification
                notification.modification_time = func.now()

                session.commit()
            return server.error("License invalid on '%s': %s" % \
                                (agent.displayname, msg))

    def repair(self, agent):
        server = self.server
        data = agent.todict()

        server.event_control.gen(EventControl.LICENSE_REPAIR_STARTED, data)

        body = server.cli_cmd('tabadmin license --repair_service', agent,
                              timeout=60*10)

        if not 'exit-status' in body or body['exit-status'] != 0:
            data['status'] = 'FAILED'
            if 'stderr' in body:
                data['error'] = body['stderr']
            else:
                data['error'] = 'License repair failed'
            server.event_control.gen(EventControl.LICENSE_REPAIR_FAILED, data)
            server.error("License repair failed on '%s'" % agent.displayname)
        else:
            data['status'] = 'OK'
            server.event_control.gen(EventControl.LICENSE_REPAIR_FINISHED, data)
        return body

    def info(self):
        """Don't do anything very active since this can run when
           in UPGRADE state, etc."""
        entry = Domain.get_by_name(self.server.domainname)
        return licensing_info(entry, self.server.environment.envid,
                              self.server.system)

    def send(self):
        # pylint: disable=too-many-return-statements
        entry = Domain.getone()
        logging.debug('license send, license_id: %s', entry.license_key)
        if not entry.license_key:
            logging.debug("license send: No license key.")

        data = self.info()
        if not 'license-type' in data:
            logging.debug("license send: No tableau license info yet.")

        try:
            body = licensing_send('/license', data, self.server.system)
        except IOError as ex:
            logging.debug("license send exception failed with status %s", ex)
            self._callfailed(str(ex))
            return {"error": str(ex)}
        except LicenseException as ex:
            logging.debug(
                "license send exception failed with status %d, reason %s",
                ex.status, ex.reason)
            self._callfailed(ex.reason, ex.status)
            return {"error": str(ex)}

        if not 'trial' in body:
            logging.debug('no trial value in reply: %s', str(body))

        if not 'expiration-time' in body:
            logging.debug("No expiration value in reply: %s", str(body))

        if 'id' in body:
            entry.domainid = int(body['id'])

        entry.trial = body['trial']
        entry.expiration_time = body['expiration-time']
        meta.Session.commit()

        self._callok()

        return body

    def _callfailed(self, reason, status=None):
        """If answered=True, it answered, but returned an invalid response."""
        session = meta.Session()

        data = {}

        # FIXME: pass as a parameter
        entry = Domain.getone()
        if not entry.contact_failures:
            entry.contact_failures = 1
        else:
            entry.contact_failures += 1

        if status == 404:
            # The license was not found.
            # Set the expiration to now.
            entry.expiration_time = func.now()
            session.commit()
            return

        if not entry.contact_time:
            # Never connected successfully to the license server.
            # Could happen on initial installation.
            # Give them 72 hours to get this sorted out by pretending
            # they contacted the server on initial attempt.
            entry.contact_time = func.now()
            session.commit()
            return

        max_silence_time = self.server.system[SystemKeys.MAX_SILENCE_TIME]
        silence_time = seconds_since(entry.contact_time)
#        print "contact_time:", entry.contact_time
#        print "timestamp thing:", datetime.datetime.utcnow()
#        print "silence_time:", silence_time, "max:", max_silence_time

        if silence_time <= max_silence_time and max_silence_time != -1:
            # It failed to phone home, but we have more time to try,
            logging.debug("silence_time: %d <= max: %d",
                              silence_time, max_silence_time)
            # If they had no expiration time (like on initial install)
            # then expire it now.
            if not entry.expiration_time:
                entry.expiration_time = func.now()
            session.commit()
            return

        data['failure_hours'] = int((datetime.datetime.utcnow() - \
                                    entry.contact_time).total_seconds() / 3600)

        logging.debug("failure hours was longer than %d: %d",
                      max_silence_time, data['failure_hours'])

        notification = self.server.notifications.get("phonehome")
        notification.description = reason
        if not status is None:
            notification.description += ', status: ' + str(status)

        data['contact_failures'] = entry.contact_failures
        data['last_contact_time'] = entry.contact_time
        if max_silence_time != -1:
            data['max_silence_hours'] = max_silence_time/(60*60)
        else:
            data['max_silence_hours'] = 96  # just to be different

        if notification.color != 'red':
            self.server.event_control.gen(EventControl.PHONE_HOME_FAILED, data)

            notification.color = 'red'
            notification.notified_color = 'red'
            # Remember when we sent the notification
            notification.modification_time = func.now()

        session.commit()

    def _callok(self):

        session = meta.Session()
        entry = Domain.getone()
        data = {'contact_failures': entry.contact_failures}

        entry.contact_failures = 0
        entry.contact_time = func.now()

        notification = self.server.notifications.get("phonehome")

        if notification.color == 'red':
            self.server.event_control.gen(EventControl.PHONE_HOME_OK, data)
            notification.modification_time = func.now()
            notification.color = 'green'
            notification.notified_color = 'green'
            notification.description = None

        session.commit()
