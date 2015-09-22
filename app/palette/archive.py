""" Archive functionality for workbooks and datasources """
# pylint: enable=missing-docstring,relative-import

from abc import ABCMeta, abstractmethod

from controller.profile import UserProfile
from controller.util import UNDEFINED

from .rest import PaletteRESTApplication

class ArchiveUserCache(dict):
    """ Cache of system_user_id -> display_name objects.
    The users table may be too big to pull in entirely so user objects
    are cached as they are looked up.
    """

    def __init__(self, envid):
        self.envid = envid
        super(ArchiveUserCache, self).__init__()

    def _get_from_db(self, system_user_id):
        """ Retrieve the object from the database. """
        user = UserProfile.get_by_system_user_id(self.envid, system_user_id)
        if not user:
            return UNDEFINED
        return user.display_name()

    def __getitem__(self, key):
        system_user_id = int(key)
        try:
            return dict.__getitem__(self, system_user_id)
        except KeyError:
            pass
        display_name = self._get_from_db(system_user_id)
        dict.__setitem__(self, system_user_id, display_name)
        return display_name


class ArchiveApplication(PaletteRESTApplication):
    """ Base class for all REST handlers. """
    __metaclass__ = ABCMeta

    ALL_SITES_PROJECTS_OPTION = 'All Sites/Projects'
    ALL_SITES_OPTION = "All Sites"
    ALL_PROJECTS_OPTION = "All Projects"

    def _site_options(self, sites):
        """ Build the config information for the site dropdown. """
        options = [{"item": self.ALL_SITES_OPTION, "id": 0}]
        for site in sites.values():
            options.append({"item": site.name, "id": site.id})
        return options

    def _site_value(self, siteid, sites):
        """ Get the display value for a given site id. """
        if siteid == 0:
            return self.ALL_SITES_OPTION
        if siteid in sites:
            return sites[siteid].name
        return None

    def _project_options(self, siteid, projects):
        """ Build the config information for the project dropdown. """
        options = [{"item": self.ALL_PROJECTS_OPTION, "id": 0}]
        for project in projects.values():
            if siteid == 0 or project.site_id == siteid:
                options.append({"item": project.name, "id": project.id})
        return options

    def _project_value(self, projectid, projects):
        """ Get the display value for a given project id. """
        if projectid == 0:
            return self.ALL_PROJECTS_OPTION
        if projectid in projects:
            return projects[projectid].name
        return None

    @abstractmethod
    def show_options(self, req):
        """ Build the options for the 'show' dropdown."""
        pass

    @abstractmethod
    def sort_options(self, req):
        """ Build the options for the 'sort' dropdown."""
        pass

    def build_config(self, req, sites, projects):
        """ Create the config options for the page.
        Depends on both sort_ and show_ options being overridden.
        """

        config = []
        config.append(self.show_options(req))
        config.append(self.sort_options(req))

        siteid = req.params_getint('site', 0)
        sitename = self._site_value(siteid, sites)
        if not sitename:
            siteid = 0
            sitename = self.ALL_SITES_OPTION
        config.append({"name": "site-dropdown",
                       "options": self._site_options(sites),
                       "id": str(siteid),
                       "value": sitename})

        projectid = req.params_getint('project', 0)
        projectname = self._project_value(projectid, projects)

        if not projectname:
            projectid = 0
            projectname = self.ALL_PROJECTS_OPTION
        config.append({"name": "project-dropdown",
                       "options": self._project_options(siteid, projects),
                       "id": str(projectid),
                       "value": projectname})
        return config
