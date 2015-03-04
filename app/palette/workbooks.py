import os

from collections import OrderedDict
from webob import exc
from paste.fileapp import FileApp

from akiri.framework import GenericWSGIApplication
import akiri.framework.sqlalchemy as meta

from controller.workbooks import WorkbookEntry, WorkbookUpdateEntry
from controller.util import UNDEFINED, safe_int
from controller.profile import UserProfile, Role
from controller.credential import CredentialEntry
from controller.sites import Site
from controller.projects import Project

from .option import DictOption
from .page import PalettePage
from .rest import required_parameters, required_role, PaletteRESTApplication

__all__ = ["WorkbookApplication"]

class CredentialMixin(object):

    PRIMARY_KEY = 'primary'
    SECONDARY_KEY = 'secondary'

    def get_cred(self, envid, name):
        return CredentialEntry.get_by_envid_key(envid, name, default=None)

class WorkbookShow(DictOption):
    """Options to show all workbooks or only for the current user."""
    NAME = 'show-dropdown'
    ALL = 0
    MINE = 1

    @classmethod
    def items(cls):
        return OrderedDict({
            cls.ALL: 'All Workbooks',
            cls.MINE: 'My Workbooks'})

    def __init__(self, valueid):
        super(WorkbookShow, self).__init__(self.NAME, valueid,
                                           self.__class__.items())

class WorkbookSort(DictOption):
    """Possible ways to sort workbooks."""
    NAME = "sort-dropdown"
    WORKBOOK = 0
    SITE = 1
    PROJECT = 2
    PUBLISHER = 3
    REVISION_DATE = 4

    @classmethod
    def items(cls):
        return OrderedDict({
            cls.WORKBOOK: 'Workbook',
            cls.SITE: 'Site',
            cls.PROJECT: 'Project',
            cls.PUBLISHER: 'Publisher',
            cls.REVISION_DATE: 'Revision Date'})

    def __init__(self, valueid):
        super(WorkbookSort, self).__init__(self.NAME, valueid,
                                           self.__class__.items())


class WorkbookApplication(PaletteRESTApplication, CredentialMixin):
    # pylint: disable=too-many-public-methods

    ALL_SITES_PROJECTS_OPTION = 'All Sites/Projects'

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
        entry = super(WorkbookApplication, self).get_cred(envid, name)
        if not entry:
            entry = CredentialEntry(envid=envid, key=name)
            meta.Session.add(entry)
        return entry

    def item_count(self, envid):
        return WorkbookEntry.count(filters={'envid':envid})

    def show_options(self, req):
        valueid = req.params_getint('show', WorkbookShow.ALL)
        return WorkbookShow(valueid).default()

    def sort_options(self, req):
        valueid = req.params_getint('sort', WorkbookSort.WORKBOOK)
        return WorkbookSort(valueid).default()

    def site_project_options(self, sites, projects):
        # estimate: < 50 projects
        options = [{'item': self.ALL_SITES_PROJECTS_OPTION, 'id': 0}]
        for site in sites.values():
            for project in projects.values():
                if project.site_id != site.id:
                    continue
                data = {'item': site.name + '/' + project.name,
                        'id': str(site.id) + ':' + str(project.id)}
                options.append(data)
        return options

    # returns id,value
    def site_project_id_value(self, req, sites, projects):
        if 'site-project' not in req.GET:
            return 0, self.ALL_SITES_PROJECTS_OPTION
        key = str(req.GET['site-project'])
        if key == '0':
            return 0, self.ALL_SITES_PROJECTS_OPTION
        tokens = key.split(':')
        if len(tokens) != 2:
            return 0, self.ALL_SITES_PROJECTS_OPTION
        try:
            site_id = int(tokens[0])
            project_id = int(tokens[1])
        except StandardError:
            return 0, self.ALL_SITES_PROJECTS_OPTION
        if site_id not in sites or project_id not in projects:
            return 0, self.ALL_SITES_PROJECTS_OPTION
        value = sites[site_id].name + '/' + projects[project_id].name
        return str(site_id) + ':' + str(project_id), value

    def build_config(self, req, sites, projects):
        # pylint: disable=no-member
        # OPTIONS is created by __setattr__ of the metaclass so pylint warning.
        config = []
        config.append(self.show_options(req))
        config.append(self.sort_options(req))

        site_project_options = self.site_project_options(sites, projects)
        spid, value = self.site_project_id_value(req, sites, projects)
        config.append({'name': 'site-project-dropdown',
                       'options': site_project_options,
                       'id': spid, 'value': value})
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

    # FIXME: covert to /workbook/<id>/note or /workbook/note/<id>
    # GET doesn't have a ready meaning.
    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('id', 'value')
    def handle_update_note(self, req):
        wuid = req.POST['id']
        update = WorkbookUpdateEntry.get_by_id(wuid)
        if not update:
            raise exc.HTTPGone()
        update.note = req.POST['value']
        meta.Session.commit()
        return {'value': update.note}

    def build_query_filters(self, req):
        filters = OrderedDict({'envid':req.envid})
        if req.remote_user.roleid == Role.NO_ADMIN:
            showid = WorkbookShow.MINE
        else:
            showid = req.params_getint('show')
            #pylint: disable=no-member
            if showid is None or showid not in WorkbookShow.items():
                showid = WorkbookShow.ALL
        if showid == WorkbookShow.MINE:
            filters['system_user_id'] = req.remote_user.system_user_id

        site_project = req.params_get('site-project', default='0')
        if site_project != '0':
            tokens = site_project.split(':')
            if len(tokens) == 2:
                site_id = safe_int(tokens[0], default=0)
                if site_id != 0:
                    filters['site_id'] = site_id
                project_id = safe_int(tokens[1], default=0)
                if project_id != 0:
                    filters['project_id'] = project_id
        return filters

    def do_query(self, req):
        filters = self.build_query_filters(req)

        query = meta.Session.query(WorkbookEntry)

        # pylint: disable=no-member
        # pylint: disable=maybe-no-member
        sort = req.params_getint('sort')
        if sort is None or sort not in WorkbookSort.items():
            sort = WorkbookSort.NAME

        if sort == WorkbookSort.SITE:
            query = query.join(Site,
                               WorkbookEntry.site_id == Site.id)
        elif sort == WorkbookSort.PROJECT:
            query = query.join(Project,
                               WorkbookEntry.project_id == Project.id)
        elif sort == WorkbookSort.PUBLISHER:
            query = query.join(UserProfile, \
                WorkbookEntry.system_user_id == UserProfile.system_user_id)

        query = WorkbookEntry.apply_filters(query, filters)

        if sort == WorkbookSort.NAME:
            query = query.order_by(WorkbookEntry.name)
        elif sort == WorkbookSort.SITE:
            query = query.order_by(Site.name, WorkbookEntry.name)
        elif sort == WorkbookSort.PROJECT:
            query = query.order_by(Project.name, WorkbookEntry.name)
        elif sort == WorkbookSort.REVISION_DATE:
            query = query.order_by(WorkbookEntry.created_at.desc())
        elif sort == WorkbookSort.PUBLISHER:
            query = query.order_by(UserProfile.friendly_name)

        limit = req.params_getint('limit', default=25)
        page = req.params_getint('page', default=1)

        offset = (page - 1) * limit
        query = query.limit(limit).offset(offset)

        return query.all()

    # FIXME: move build options to a separate file.
    def handle_get(self, req):

        entries = self.do_query(req)

        # lookup caches
        users = {}
        sites = Site.cache(req.envid)
        projects = Project.cache(req.envid)

        workbooks = []
        for entry in entries:
            data = entry.todict(pretty=True)

            updates = []
            for update in entry.updates:
                d = update.todict(pretty=True)
                d['username'] = self.getuser(req.envid,
                                             update.system_user_id,
                                             users)
                if 'url' in d and d['url']:
                    # FIXME: make this configurable
                    d['url'] = '/data/workbook-archive/' + d['url']
                updates.append(d)
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

            workbooks.append(data)

        return {'workbooks': workbooks,
                'config': self.build_config(req, sites, projects),
                'item-count': self.item_count(req.envid)
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


class WorkbookData(GenericWSGIApplication):

    def __init__(self, path):
        super(WorkbookData, self).__init__()
        self.path = os.path.abspath(path)
        if not os.path.isdir(self.path):
            os.makedirs(self.path)

    def check_permission(self, req, update):
        if req.remote_user.roleid > Role.NO_ADMIN:
            return True
        if req.remote_user.system_user_id == update.workbook.system_user_id:
            return True

    def service_GET(self, req):
        path_info = req.environ['PATH_INFO']
        if path_info.startswith('/'):
            path_info = path_info[1:]

        update = WorkbookUpdateEntry.get_by_url(path_info, default=None)
        if update is None:
            return exc.HTTPNotFound()

        if not self.check_permission(req, update):
            return exc.HTTPForbidden()

        path = os.path.join(self.path, path_info)
        if not os.path.isfile(path):
            return exc.HTTPGone()
        return FileApp(path)


class WorkbookArchive(PalettePage):
    TEMPLATE = 'workbook.mako'
    active = 'workbook-archive'
