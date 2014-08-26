import os
import socket

from webob import exc
from paste.fileapp import FileApp

from akiri.framework.api import RESTApplication, BaseApplication
from akiri.framework.config import store

from akiri.framework.ext.sqlalchemy import meta

from controller.environment import Environment
from controller.workbooks import WorkbookEntry, WorkbookUpdateEntry
from controller.util import UNDEFINED
from controller.profile import UserProfile, Role
from controller.credential import CredentialEntry
from controller.util import DATEFMT
from controller.sites import Site
from controller.projects import Project

from page import PalettePage, FAKEPW
from rest import PaletteRESTHandler
from rest import translate_remote_user, required_parameters, required_role

__all__ = ["WorkbookApplication"]

class CredentialMixin(object):

    PRIMARY_KEY = 'primary'
    SECONDARY_KEY = 'secondary'

    def get_cred(self, name):
        envid = self.environment.envid
        return CredentialEntry.get_by_envid_key(envid, name, default=None)

class WorkbookApplication(PaletteRESTHandler, CredentialMixin):

    NAME = 'workbooks'

    def getuser_fromdb(self, system_user_id):
        if system_user_id < 0:
            return UNDEFINED
        user = UserProfile.get_by_system_users_id(system_user_id)
        if not user:
            return UNDEFINED
        return user.display_name()

    def getuser(self, system_user_id, cache={}):
        if system_user_id in cache:
            return cache[system_user_id]
        user = self.getuser_fromdb(system_user_id)
        cache[system_user_id] = user
        return user

    def get_cred(self, name):
        entry = super(WorkbookApplication, self).get_cred(name)
        if not entry:
            entry = CredentialEntry(envid=self.environment.envid, key=name)
            meta.Session.add(entry)
        return entry

    def get_site(self, siteid, cache={}):
        if siteid in cache:
            return cache[siteid]
        envid = self.environment.envid
        entry = Site.get(envid, siteid, default=None)
        name = entry and entry.name or ''
        cache[siteid] = name
        return name

    def get_project(self, projectid, cache={}):
        if projectid in cache:
            return cache[projectid]
        envid = self.environment.envid
        entry = Project.get(envid, projectid, default=None)
        name = entry and entry.name or ''
        cache[projectid] = name
        return name

    @required_parameters('value')
    def handle_user_POST(self, req, cred):
        value = req.POST['value']
        cred.user = value
        meta.Session.commit()
        return {'value':value}

    @required_parameters('value')
    def handle_passwd_POST(self, req, cred):
        value = req.POST['value']
        cred.setpasswd(value)
        meta.Session.commit()
        return {'value':value}

    @required_role(Role.MANAGER_ADMIN)
    def handle_user(self, req, key):
        cred = self.get_cred(key)
        if req.method == 'POST':
            return self.handle_user_POST(req, cred)
        value = cred and cred.user or ''
        return {'value': value}
        
    @required_role(Role.MANAGER_ADMIN)
    def handle_passwd(self, req, key):
        cred = self.get_cred(key)
        if req.method == 'POST':
            return self.handle_passwd_POST(req, cred)
        value = cred and FAKEPW or ''
        return {'value': value}

    # GET doesn't have a ready meaning.
    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('id', 'value')
    def handle_update_note(self, req     ):
        wuid = req.POST['id']
        update = WorkbookUpdateEntry.get_by_id(wuid)
        if not update:
            raise exc.HTTPGone()
        update.note = req.POST['value']
        meta.Session.commit()
        return {'value': update.note}

    @translate_remote_user
    def handle_get(self, req):
        users = {}; sites={}; projects={}  # lookup caches
        envid = self.environment.envid

        if req.remote_user.roleid > Role.NO_ADMIN:
            entries = WorkbookEntry.get_all_by_envid(envid)
        else:
            system_user_id = req.remote_user.system_users_id
            entries = WorkbookEntry.get_all_by_system_user(envid,
                                                           system_user_id)

        workbooks = []
        for entry in entries:
            data = entry.todict(pretty=True)

            updates = []
            for update in entry.updates:
                d = update.todict(pretty=True)
                d['username'] = self.getuser(update.system_user_id, users)
                if 'url' not in d or not d['url']:
                    d['url'] = '#'
                else:
                    # FIXME: make this configurable
                    d['url'] = '/data/workbook-archive/' + d['url']
                updates.append(d)
            data['updates'] = updates

            current = updates[0]
            data['last-updated-by'] = d['username']
            data['last-updated-at'] = d['timestamp']
            data['url'] = d['url']

            data['site'] = self.get_site(entry.site_id, cache=sites)
            data['project'] = self.get_project(entry.project_id, cache=projects)

            workbooks.append(data)

        return {'workbooks': workbooks}

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


class TabcmdPage(PalettePage, CredentialMixin):
    TEMPLATE = "tabcmd.mako"
    active = 'tabcmd'
    expanded = True
    required_role = Role.MANAGER_ADMIN

    def render(self, req, obj=None):
        primary = self.get_cred(self.PRIMARY_KEY)
        if primary:
            req.primary_user = primary.user
            req.primary_pw = primary.embedded and FAKEPW or ''
        else:
            req.primary_user = req.primary_pw = ''
        secondary = self.get_cred(self.SECONDARY_KEY)
        if secondary:
            req.secondary_user = secondary.user
            req.secondary_pw = secondary.embedded and FAKEPW or ''
        else:
            req.secondary_user = req.secondary_pw = ''
        return super(TabcmdPage, self).render(req, obj=obj)

def make_tabcmd(global_conf):
    return TabcmdPage(global_conf)


class WorkbookData(BaseApplication):

    def __init__(self, global_conf, path=None):
        super(WorkbookData, self).__init__(global_conf)
        if not path:
            dirname = os.path.dirname(global_conf['__file__'])
            path = os.path.join(dirname, 'data', 'workbook-archive')
        self.path = os.path.abspath(path)
        if not os.path.isdir(self.path):
            os.makedirs(self.path)

    def __getattr__(self, name):
        if name == 'environment':
            return Environment.get()
        raise AttributeError(name)

    def check_permission(self, req, update):
        if req.remote_user.roleid > Role.NO_ADMIN:
            return True
        if req.remote_user.system_users_id == update.workbook.system_user_id:
            return True

    @translate_remote_user
    def handle(self, req):
        envid = self.environment.envid

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
    return WorkbookData(global_conf)
