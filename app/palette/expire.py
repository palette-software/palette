from datetime import datetime

from webob import exc

from akiri.framework import GenericWSGI

from controller.licensing import LicenseEntry

LICENSE_EXPIRED = 'http://www.palette-software.com/license-expired'
TRIAL_EXPIRED = 'http://www.palette-software.com/trial-expired'

class ExpireMiddleware(GenericWSGI):
    """Check for expired trials/licenses and redirect if necessary."""
    def service(self, req):
        if req.palette_domain.expiration_time is None \
                or datetime.now() < req.palette_domain.expiration_time:
            return None
        if req.palette_domain.trial:
            location = TRIAL_EXPIRED
        else:
            location = LICENSE_EXPIRED

        location += '?key=' + req.palette_domain.license_key

        for entry in LicenseEntry.all():
            location += '&type=' + entry.gettype()
            if entry.interactors:
                location += '&n=' + entry.interactors
            else:
                location += '&n=0'
        raise exc.HTTPTemporaryRedirect(location=location)
        

def make_expire_filter(app, global_conf):
    # pylint: disable=unused-argument
    return ExpireMiddleware(app)
