from datetime import datetime
from webob import exc
from sqlalchemy.orm.exc import NoResultFound

from akiri.framework import GenericWSGI
import akiri.framework.sqlalchemy as meta

from controller.licensing import LicenseEntry
from controller.agent import Agent
from controller.general import SystemConfig

LICENSE_EXPIRED = 'https://licensing.palette-software.com/license-expired'
TRIAL_EXPIRED = 'https://licensing.palette-software.com/trial-expired'
PHONEHOME_FAILED = \
                'https://licensing.palette-software.com/licensing-unavailable'

class ExpireMiddleware(GenericWSGI):
    """Check for expired trials/licenses/phonehome-fialures and
       redirect if necessary."""
    def service(self, req):
        # pylint: disable=too-many-branches
#        print "contact_time:", req.palette_domain.contact_time

        scfg = SystemConfig(req.system)
        max_silence_time = scfg.max_silence_time
        if req.palette_domain.expiration_time and \
                datetime.utcnow() > req.palette_domain.expiration_time:
            if req.palette_domain.trial:
                location = TRIAL_EXPIRED
            else:
                location = LICENSE_EXPIRED
        elif max_silence_time != -1 and \
            req.palette_domain.contact_time and \
                    (datetime.utcnow() - \
                    req.palette_domain.contact_time).total_seconds() > \
                                            max_silence_time:
            location = PHONEHOME_FAILED
        else:
            return None

        if req.palette_domain.license_key:
            location += '?key=' + req.palette_domain.license_key
        else:
            location += '?key=' # development only

        for entry in LicenseEntry.all():
            location += '&type=' + entry.gettype().lower()
            if entry.interactors:
                location += '&n=' + str(entry.interactors)
            else:
                try:
                    agent_entry = meta.Session.query(Agent).\
                        filter(Agent.agentid == entry.agentid).\
                        one()
                except NoResultFound:
                    print 'expire: No agent with agentid', entry.agentid
                    location += '&n=0'
                else:
                    location += '&n=' + str(agent_entry.processor_count)

        raise exc.HTTPTemporaryRedirect(location=location)


def make_expire_filter(app, global_conf):
    # pylint: disable=unused-argument
    return ExpireMiddleware(app)
