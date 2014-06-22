from webob import exc

from akiri.framework.api import Page

from controller.profile import Role

class PalettePageMixin(object):
    # The active page on the mainNav
    active = ''
    # Whether or not to show the expanded configure items.
    expanded = False;
    # Whether or not to show the expanded integration items.
    integration = False

class PalettePage(Page, PalettePageMixin):
    required_role = None

    def render(self, req, obj=None):
        if not self.required_role is None:
            if req.remote_user.roleid < self.required_role:
                raise exc.HTTPForbidden
        return super(PalettePage, self).render(req, obj=obj)
