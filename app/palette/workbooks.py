import os

from collections import OrderedDict
from webob import exc
from paste.fileapp import FileApp

from akiri.framework.api import BaseApplication

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from controller.workbooks import WorkbookEntry, WorkbookUpdateEntry
from controller.util import UNDEFINED, safe_int
from controller.profile import UserProfile, Role
from controller.credential import CredentialEntry
from controller.sites import Site
from controller.projects import Project

from page import FAKEPW
from rest import PaletteRESTHandler
from rest import required_parameters, required_role

__all__ = ["WorkbookApplication"]

class CredentialMixin(object):

    PRIMARY_KEY = 'primary'
    SECONDARY_KEY = 'secondary'

    def get_cred(self, envid, name):
        return CredentialEntry.get_by_envid_key(envid, name, default=None)

class StaticOptionType(type):
    def __getattr__(cls, name):
        if name == 'ITEMS':
            return cls.items()
        if name == 'OPTIONS':
            options = []
            for key, value in cls.ITEMS.items():
                options.append({'option': value, 'id': key})
            return options
        raise AttributeError(name)

class BaseStaticOption(object):
    __metaclass__ = StaticOptionType

    @classmethod
    def get(cls, req, name, default=0):
        #pylint: disable=no-member
        if name not in req.GET:
            return default
        try:
            value = int(req.GET[name])
        except StandardError:
            return default
        if value not in cls.ITEMS:
            return default
        return value

    @classmethod
    def name(cls, key):
        #pylint: disable=no-member
        if key in cls.ITEMS:
            return cls.ITEMS[key]
        else:
            return None

class WorkbookShow(BaseStaticOption):
    ALL = 0
    MINE = 1

    @classmethod
    def items(cls):
        return OrderedDict({cls.ALL:'All Workbooks', cls.MINE:'My Workbooks'})

class WorkbookSort(BaseStaticOption):
    NAME = 0
    SITE = 1
    PROJECT = 2
    PUBLISHER = 3
    REVISION_DATE = 4

    @classmethod
    def items(cls):
        return OrderedDict({cls.NAME:'Workbook', cls.SITE:'Site',
                            cls.PROJECT:'Project', cls.PUBLISHER:'Publisher',
                            cls.REVISION_DATE:'Revision Date'})

class WorkbookApplication(PaletteRESTHandler, CredentialMixin):

    NAME = 'workbooks'

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

    def site_options(self, sites):
        options = [{'option': 'All Sites', 'id': 0}]
        for site in sites.values():
            data = {'option':site.name, 'id':site.siteid}
            options.append(data)
        return options

    def project_options(self, projects):
        options = [{'option': 'All Projects', 'id': 0}]
        for project in projects.values():
            data = {'option':project.name, 'id':project.projectid}
            options.append(data)
        return options

    def site_project_options(self, sites, projects):
        # estimate: < 50 projects
        options = [{'option': self.ALL_SITES_PROJECTS_OPTION, 'id': 0}]
        for site in sites.values():
            for project in projects.values():
                if project.site_id != site.siteid:
                    continue
                data = {'option': site.name + '/' + project.name,
                        'id': str(site.siteid) + ':' + str(project.projectid)}
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
            siteid = int(tokens[0])
            projectid = int(tokens[1])
        except StandardError:
            return 0, self.ALL_SITES_PROJECTS_OPTION
        if siteid not in sites or projectid not in projects:
            return 0, self.ALL_SITES_PROJECTS_OPTION
        value = sites[siteid].name + '/' + projects[projectid].name
        return str(siteid) + ':' + str(projectid), value

    def build_config(self, req, sites, projects):
        # pylint: disable=no-member
        # OPTIONS is created by __setattr__ of the metaclass so pylint warning.
        config = []
        show_options = WorkbookShow.OPTIONS
        showid = WorkbookShow.get(req, 'show')

        config.append({'name': 'show', 'options': show_options,
                       'id': showid, 'value': WorkbookShow.name(showid)})

        sort_options = WorkbookSort.OPTIONS
        sortid = WorkbookSort.get(req, 'sort')

        config.append({'name': 'sort', 'options': sort_options,
                       'id': sortid, 'value': WorkbookSort.name(sortid)})

        site_project_options = self.site_project_options(sites, projects)
        spid, value = self.site_project_id_value(req, sites, projects)
        config.append({'name': 'site-project', 'options': site_project_options,
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
        value = cred and FAKEPW or ''
        return {'value': value}

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
            showid = req.getint('show')
            #pylint: disable=no-member
            if showid is None or showid not in WorkbookShow.ITEMS:
                showid = WorkbookShow.ALL
        if showid == WorkbookShow.MINE:
            filters['system_user_id'] = req.remote_user.system_user_id

        site_project = req.get('site-project', default='0')
        if site_project != '0':
            tokens = site_project.split(':')
            if len(tokens) == 2:
                siteid = safe_int(tokens[0], default=0)
                if siteid != 0:
                    filters['site_id'] = siteid
                projectid = safe_int(tokens[1], default=0)
                if projectid != 0:
                    filters['project_id'] = projectid
        return filters

    def do_query(self, req):
        filters = self.build_query_filters(req)

        query = meta.Session.query(WorkbookEntry)

        # pylint: disable=no-member
        # pylint: disable=maybe-no-member
        sort = req.getint('sort')
        if sort is None or sort not in WorkbookSort.ITEMS:
            sort = WorkbookSort.NAME

        if sort == WorkbookSort.SITE:
            query = query.join(Site,
                               WorkbookEntry.site_id == Site.siteid)
        elif sort == WorkbookSort.PROJECT:
            query = query.join(Project,
                               WorkbookEntry.project_id == Project.projectid)
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

        limit = req.getint('limit', default=25)
        page = req.getint('page', default=1)

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
                if 'url' not in d or not d['url']:
                    d['url'] = '#'
                else:
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

    def handle(self, req):
        path_info = self.base_path_info(req)
        if path_info == 'primary/user':
            return self.handle_user(req, key=self.PRIMARY_KEY)
        elif path_info == 'primary/password':
            return self.handle_passwd(req, key=self.PRIMARY_KEY)
        elif path_info == 'secondary/user':
            return self.handle_user(req, key=self.SECONDARY_KEY)
        elif path_info == 'secondary/password':
            return self.handle_passwd(req, key=self.SECONDARY_KEY)
        elif path_info == 'updates/note':
            return self.handle_update_note(req)
        elif path_info:
            raise exc.HTTPBadRequest()

        if req.method == "GET":
            return self.handle_get(req)
        else:
            raise exc.HTTPBadRequest()


class WorkbookData(BaseApplication):

    def __init__(self, global_conf, path=None):
        super(WorkbookData, self).__init__(global_conf)
        if not path:
            dirname = os.path.dirname(global_conf['__file__'])
            path = os.path.join(dirname, 'data', 'workbook-archive')
        self.path = os.path.abspath(path)
        if not os.path.isdir(self.path):
            os.makedirs(self.path)

    def check_permission(self, req, update):
        if req.remote_user.roleid > Role.NO_ADMIN:
            return True
        if req.remote_user.system_user_id == update.workbook.system_user_id:
            return True

    def handle(self, req):
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

def make_workbook_data(global_conf, path=None):
    return WorkbookData(global_conf, path=path)
