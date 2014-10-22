from webob import exc

from akiri.framework.api import Page

FAKEPW = '********'

class PalettePageMixin(object):
    # The active page on the mainNav
    active = ''
    # Whether or not to show the expanded configure items.
    expanded = False
    # Whether or not to show the expanded integration items.
    integration = False
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

    def preprocess(self, req, obj):
        # pylint: disable=attribute-defined-outside-init
        
        # req.remote_user can possibly be None if AD authentication works,
        # but there is a problem importing the user database from Tableau.
        if req.remote_user is None:
            # FIXME: print to the error log?
            raise exc.HTTPTemporaryRedirect(location='/login')
        if not self.required_role is None:
            if req.remote_user.roleid < self.required_role:
                raise exc.HTTPForbidden
        if obj is None:
            obj = self
        if 'status_color' in req.cookies:
            color = req.cookies['status_color']
            obj.status_class = self.build_status_class(color)
        else:
            obj.status_class = ''
        if 'status_text' in req.cookies:
            obj.status_text = req.cookies['status_text'].replace("_", " ")
        else:
            obj.status_text = ''
        return obj

class PalettePage(Page, PalettePageMixin):

    def render(self, req, obj=None):
        obj = self.preprocess(req, obj)
        return super(PalettePage, self).render(req, obj=obj)
