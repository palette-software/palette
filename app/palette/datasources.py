import os

from collections import OrderedDict
from webob import exc
from paste.fileapp import DataApp

from akiri.framework import GenericWSGIApplication, ENVIRON_PREFIX
import akiri.framework.sqlalchemy as meta

from controller.datasources import DataSourceEntry, DataSourceUpdateEntry
from controller.util import UNDEFINED
from controller.profile import UserProfile, Role
from controller.credential import CredentialEntry
from controller.sites import Site
from controller.projects import Project
from controller.system import SystemKeys

from .option import DictOption
from .page import PalettePage
from .rest import required_parameters, required_role, PaletteRESTApplication
from .mixin import CredentialMixin

__all__ = ["DatasourceApplication"]

class DatasourceShow(DictOption):
    """Options to show all datasources or only for the current user."""
    NAME = 'show-dropdown'
    ALL = 0
    MINE = 1

    @classmethod
    def items(cls):
        return OrderedDict({
            cls.ALL: 'All Datasources',
            cls.MINE: 'My Datasources'})

    def __init__(self, valueid):
        super(DatasourceShow, self).__init__(self.NAME, valueid,
                                           self.__class__.items())

class DatasourceSort(DictOption):
    """Possible ways to sort datasources."""
    NAME = "sort-dropdown"
    DATASOURCE = 0
    # fixme: put in a common subclass
    SITE = 1
    PROJECT = 2
    PUBLISHER = 3
    REVISION_DATE = 4

    @classmethod
    def items(cls, req):
        info = OrderedDict({
            cls.DATASOURCE: 'Datasource',
            cls.SITE: 'Site',
            cls.PROJECT: 'Project',
            cls.PUBLISHER: 'Publisher',
            cls.REVISION_DATE: 'Revision Date'})

        if req.remote_user.roleid == Role.NO_ADMIN:
            del info[cls.PUBLISHER]

        return info

    def __init__(self, valueid, req):
        super(DatasourceSort, self).__init__(self.NAME, valueid,
                                           self.__class__.items(req))


# fixme: almost all this needs to be in a common subclass
class DatasourceApplication(PaletteRESTApplication, CredentialMixin):
    # pylint: disable=too-many-public-methods

    ALL_SITES_PROJECTS_OPTION = 'All Sites/Projects'
    ALL_SITES_OPTION = "All Sites"
    ALL_PROJECTS_OPTION = "All Projects"

    def getuser_fromdb(self, envid, system_user_id):
        if system_user_id < 0:
            return UNDEFINED
        user = UserProfile.get_by_system_user_id(envid, system_user_id)
        if not user:
            return UNDEFINED
        return user.display_name()

    def getuser(self, envid, system_user_id, cache=None):
        if cache is None:
            cache = {}
        if system_user_id in cache:
            return cache[system_user_id]
        user = self.getuser_fromdb(envid, system_user_id)
        cache[system_user_id] = user
        return user

    def get_cred(self, envid, name):
        entry = super(DatasourceApplication, self).get_cred(envid, name)
        if not entry:
            entry = CredentialEntry(envid=envid, key=name)
            meta.Session.add(entry)
        return entry

    def show_options(self, req):
        valueid = req.params_getint('show', DatasourceShow.ALL)
        return DatasourceShow(valueid).default()

    def sort_options(self, req):
        valueid = req.params_getint('sort', DatasourceSort.DATASOURCE)
        return DatasourceSort(valueid, req).default()

    def site_options(self, sites):
        options = [{"item": self.ALL_SITES_OPTION, "id": 0}]
        for site in sites.values():
            options.append({"item": site.name, "id": site.id})
        return options

    def site_value(self, siteid, sites):
        if siteid == 0:
            return self.ALL_SITES_OPTION
        if siteid in sites:
            return sites[siteid].name
        return None

    def project_options(self, siteid, projects):
        options = [{"item": self.ALL_PROJECTS_OPTION, "id": 0}]
        for project in projects.values():
            if siteid == 0 or project.site_id == siteid:
                options.append({"item": project.name, "id": project.id})
        return options

    def project_value(self, projectid, projects):
        if projectid == 0:
            return self.ALL_PROJECTS_OPTION
        if projectid in projects:
            return projects[projectid].name
        return None

    def build_config(self, req, sites, projects):
        # pylint: disable=no-member
        # OPTIONS is created by __setattr__ of the metaclass so pylint warning.
        config = []
        config.append(self.show_options(req))
        config.append(self.sort_options(req))

        siteid = req.params_getint('site', 0)
        sitename = self.site_value(siteid, sites)
        if not sitename:
            siteid = 0
            sitename = self.ALL_SITES_OPTION
        config.append({"name": "site-dropdown",
                       "options": self.site_options(sites),
                       "id": str(siteid),
                       "value": sitename})

        projectid = req.params_getint('project', 0)
        projectname = self.project_value(projectid, projects)

        if not projectname:
            projectid = 0
            projectname = self.ALL_PROJECTS_OPTION
        config.append({"name": "project-dropdown",
                       "options": self.project_options(siteid, projects),
                       "id": str(projectid),
                       "value": projectname})
        return config


    @required_parameters('value')
    # pylint: disable=invalid-name
    def handle_user_POST(self, req, cred):
        value = req.POST['value']
        cred.user = value
        meta.Session.commit()
        return {'value':value}

    @required_parameters('value')
    # pylint: disable=invalid-name
    def handle_passwd_POST(self, req, cred):
        value = req.POST['value']
        cred.setpasswd(value)
        meta.Session.commit()
        return {'value':value}

    @required_role(Role.MANAGER_ADMIN)
    def handle_user(self, req, key):
        cred = self.get_cred(req.envid, key)
        if req.method == 'POST':
            return self.handle_user_POST(req, cred)
        value = cred and cred.user or ''
        return {'value': value}

    @required_role(Role.MANAGER_ADMIN)
    def handle_passwd(self, req, key):
        cred = self.get_cred(req.envid, key)
        if req.method == 'POST':
            return self.handle_passwd_POST(req, cred)
        return {'value': cred}

    # FIXME: covert to /datasource/<id>/note or /datasource/note/<id>
    # GET doesn't have a ready meaning.
    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('id', 'value')
    def handle_update_note(self, req):
        wuid = req.POST['id']
        update = DataSourceUpdateEntry.get_by_id(wuid)
        if not update:
            raise exc.HTTPGone()
        update.note = req.POST['value']
        meta.Session.commit()
        return {'value': update.note}

    def build_query_filters(self, req):
        filters = OrderedDict({'envid':req.envid})
        if req.remote_user.roleid == Role.NO_ADMIN:
            showid = DatasourceShow.MINE
        else:
            showid = req.params_getint('show')
            #pylint: disable=no-member
            if showid is None or showid not in DatasourceShow.items():
                showid = DatasourceShow.ALL
        if showid == DatasourceShow.MINE:
            filters['system_user_id'] = req.remote_user.system_user_id

        site_id = req.params_getint('site', default=0)
        if site_id != 0:
            filters['site_id'] = site_id
        project_id = req.params_getint('project', default=0)
        if project_id != 0:
            filters['project_id'] = project_id

        return filters

    def do_query(self, req, filters):
        query = meta.Session.query(DataSourceEntry)

        # pylint: disable=no-member
        # pylint: disable=maybe-no-member
        sort = req.params_getint('sort')
        if sort is None or sort not in DatasourceSort.items(req):
            sort = DatasourceSort.DATASOURCE

        if sort == DatasourceSort.SITE:
            query = query.join(Site,
                               DataSourceEntry.site_id == Site.id)
        elif sort == DatasourceSort.PROJECT:
            query = query.join(Project,
                               DataSourceEntry.project_id == Project.id)
        elif sort == DatasourceSort.PUBLISHER:
            query = query.join(UserProfile, \
                DataSourceEntry.system_user_id == UserProfile.system_user_id)

        query = DataSourceEntry.apply_filters(query, filters)

        if sort == DatasourceSort.DATASOURCE:
            query = query.order_by(DataSourceEntry.name)
        elif sort == DatasourceSort.SITE:
            query = query.order_by(Site.name, DataSourceEntry.name)
        elif sort == DatasourceSort.PROJECT:
            query = query.order_by(Project.name, DataSourceEntry.name)
        elif sort == DatasourceSort.REVISION_DATE:
            query = query.order_by(DataSourceEntry.created_at.desc())
        elif sort == DatasourceSort.PUBLISHER:
            query = query.order_by(UserProfile.friendly_name)
        else:
            # Show that something is wrong.
            raise exc.HTTPNotFound()

        limit = req.params_getint('limit', default=25)
        page = req.params_getint('page', default=1)

        offset = (page - 1) * limit
        query = query.limit(limit).offset(offset)

        return query.all()

    def _build_updates_for_datasources(self, entry, users):
        """ Build a list of updates for the specified datasource entry."""
        updates = []
        for update in entry.updates:
            data = update.todict(pretty=True)
            data['username'] = self.getuser(entry.envid,
                                            update.system_user_id,
                                            users)
            if 'url' in data and data['url']:
                # FIXME: make this configurable
                data['url'] = '/data/datasource-archive/' + data['url']
            updates.append(data)
        return updates

    # FIXME: move build options to a separate file.
    def handle_get(self, req):
        if not req.system[SystemKeys.ARCHIVE_ENABLED]:
            return {'datasources': [],
                    'item-count': 0}

        filters = self.build_query_filters(req)
        entries = self.do_query(req, filters)
        count = DataSourceEntry.count(filters=filters)

        # lookup caches
        users = {}
        sites = Site.cache(req.envid)
        projects = Project.cache(req.envid)

        datasources = []
        for entry in entries:
            data = entry.todict(pretty=True)

            updates = self._build_updates_for_datasources(entry, users)
            data['updates'] = updates

            if updates:
                # slight change that the first update is not yet committed.
                current = updates[0]
                data['last-updated-by'] = current['username']
                data['last-updated-at'] = current['timestamp']
                data['current-revision'] = current['revision']
                if 'url' in current and current['url']:
                    data['url'] = current['url']

            if entry.site_id in sites:
                data['site'] = sites[entry.site_id].name
            if entry.project_id in projects:
                data['project'] = projects[entry.project_id].name

            datasources.append(data)

        if req.remote_user.roleid == Role.NO_ADMIN:
            publisher_only = True
        else:
            publisher_only = False

        return {'datasources': datasources,
                'config': self.build_config(req, sites, projects),
                'item-count': count,
                'publisher-only': publisher_only
        }

    # FIXME: route correctly.
    # FIXME: primary/secondary now (likely) unused, remove.
    def service(self, req):
        if 'action' in req.environ:
            action = req.environ['action']
            if action == 'primary/user':
                return self.handle_user(req, key=self.PRIMARY_KEY)
            elif action == 'primary/password':
                return self.handle_passwd(req, key=self.PRIMARY_KEY)
            elif action == 'secondary/user':
                return self.handle_user(req, key=self.SECONDARY_KEY)
            elif action == 'secondary/password':
                return self.handle_passwd(req, key=self.SECONDARY_KEY)
            elif action == 'updates/note':
                return self.handle_update_note(req)
            raise exc.HTTPNotFound()

        if req.method == "GET":
            return self.handle_get(req)
        else:
            raise exc.HTTPBadRequest()


class DatasourceData(GenericWSGIApplication):

    def __init__(self, path):
        super(DatasourceData, self).__init__()
        self.path = os.path.abspath(path)
        if not os.path.isdir(self.path):
            os.makedirs(self.path)

    def check_permission(self, req, update):
        if req.remote_user.roleid > Role.NO_ADMIN:
            return True
        if req.remote_user.system_user_id == update.datasource.system_user_id:
            return True
        return False

    def service_GET(self, req):
        datasource_name = req.environ[ENVIRON_PREFIX+'name']
        update = DataSourceUpdateEntry.get_by_url(datasource_name, default=None)
        if update is None:
            return exc.HTTPNotFound()

        if not self.check_permission(req, update):
            return exc.HTTPForbidden()

        return DataApp(update.tds)


class DatasourceArchive(PalettePage):
    TEMPLATE = 'datasource.mako'
    active = 'datasource-archive'