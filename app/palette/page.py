import os
import pkg_resources
from mako.lookup import TemplateLookup
from webob import exc

from akiri.framework import GenericWSGIApplication
import akiri.framework.sqlalchemy as meta

from controller.profile import UserProfile

class Page(GenericWSGIApplication):
    """Generic Page base class - for both 'internal' and 'external' pages."""
    # pylint: disable=no-member
    def __init__(self):
        super(Page, self).__init__()
        modname = self.__class__.__module__
        directory = pkg_resources.resource_filename(modname, 'templates')
        self.template_lookup_directories = [os.path.abspath(directory)]

    def render(self, req, obj=None):
        lookup = TemplateLookup(directories=self.template_lookup_directories)
        if obj is None:
            obj = self
        template = lookup.get_template(self.TEMPLATE)
        if req.remote_user:
            UserProfile.update_timestamp(req.remote_user)
            meta.Session.commit()
        return template.render(obj=obj, req=req)

    def service_GET(self, req):
        return self.render(req)

class PalettePage(Page):
    # The active page on the mainNav
    active = ''
    # Archive expanded?
    archive = False
    # Configuration expanded?
    expanded = False
    # minimum capability required
    required_role = None

    def build_status_class(self, color):
        if color == 'green':
            return 'fa-check-circle green'
        if color == 'yellow':
            return 'fa-exclamation-circle yellow'
        if color == 'red':
            return 'fa-times-circle red'
        return ''

    def render(self, req, obj=None):
        # pylint: disable=attribute-defined-outside-init
        # req.remote_user can possibly be None if AD authentication works,
        # but there is a problem importing the user database from Tableau.
        if req.remote_user is None:
            # FIXME: print to the error log?
            raise exc.HTTPTemporaryRedirect(location='/login')
        if not self.required_role is None:
            if req.remote_user.roleid < self.required_role:
                raise exc.HTTPForbidden

        if 'status_color' in req.cookies:
            color = req.cookies['status_color']
            self.status_class = self.build_status_class(color)
        else:
            self.status_class = ''
        if 'status_text' in req.cookies:
            self.status_text = req.cookies['status_text'].replace("_", " ")
        else:
            self.status_text = ''
        return super(PalettePage, self).render(req, obj=self)

