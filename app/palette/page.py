from akiri.framework.api import Page

class PalettePageMixin(object):
    # The active page on the mainNav
    active = ''
    # Whether or not to show the expanded configure items.
    expanded = False;
    # Whether or not to show the expanded integration items.
    integration = False

class PalettePage(Page, PalettePageMixin):
    pass;
