""" The workbook archive. """

from collections import OrderedDict
from webob import exc, Response

from akiri.framework import GenericWSGIApplication, ENVIRON_PREFIX
import akiri.framework.sqlalchemy as meta

from controller.workbooks import WorkbookEntry, WorkbookUpdateEntry
from controller.profile import UserProfile, Role
from controller.sites import Site
from controller.projects import Project
from controller.system import SystemKeys

from .archive import ArchiveApplication, ArchiveUserCache
from .option import DictOption
from .page import PalettePage
from .rest import required_parameters, required_role

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
    def items(cls, req):
        info = OrderedDict({
            cls.WORKBOOK: 'Workbook',
            cls.SITE: 'Site',
            cls.PROJECT: 'Project',
            cls.PUBLISHER: 'Publisher',
            cls.REVISION_DATE: 'Revision Date'})

        if req.remote_user.roleid == Role.NO_ADMIN:
            del info[cls.PUBLISHER]

        return info

    def __init__(self, valueid, req):
        super(WorkbookSort, self).__init__(self.NAME, valueid,
                                           self.__class__.items(req))


class WorkbookApplication(ArchiveApplication):
    """ The REST application for the workbook archive page. """

    def show_options(self, req):
        valueid = req.params_getint('show', WorkbookShow.ALL)
        return WorkbookShow(valueid).default()

    def sort_options(self, req):
        valueid = req.params_getint('sort', WorkbookSort.WORKBOOK)
        return WorkbookSort(valueid, req).default()

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

        site_id = req.params_getint('site', default=0)
        if site_id != 0:
            filters['site_id'] = site_id
        project_id = req.params_getint('project', default=0)
        if project_id != 0:
            filters['project_id'] = project_id

        return filters

    def do_query(self, req, filters):
        query = meta.Session.query(WorkbookEntry)

        # pylint: disable=no-member
        # pylint: disable=maybe-no-member
        sort = req.params_getint('sort')
        if sort is None or sort not in WorkbookSort.items(req):
            sort = WorkbookSort.WORKBOOK

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

        if sort == WorkbookSort.WORKBOOK:
            query = query.order_by(WorkbookEntry.name)
        elif sort == WorkbookSort.SITE:
            query = query.order_by(Site.name, WorkbookEntry.name)
        elif sort == WorkbookSort.PROJECT:
            query = query.order_by(Project.name, WorkbookEntry.name)
        elif sort == WorkbookSort.REVISION_DATE:
            query = query.order_by(WorkbookEntry.created_at.desc())
        elif sort == WorkbookSort.PUBLISHER:
            query = query.order_by(UserProfile.friendly_name)
        else:
            # Show that something is wrong.
            raise exc.HTTPNotFound()

        limit = req.params_getint('limit', default=25)
        page = req.params_getint('page', default=1)

        offset = (page - 1) * limit
        query = query.limit(limit).offset(offset)

        return query.all()

    def _build_updates_for_workbook(self, entry, users):
        """ Build a list of updates for the specified workbook entry."""
        updates = []
        for update in entry.updates:
            data = update.todict(pretty=True)
            data['username'] = users[update.system_user_id]
            if 'url' in data and data['url']:
                # FIXME: make this configurable
                data['url'] = '/data/workbook-archive/' + data['url']
            updates.append(data)
        return updates

    # FIXME: move build options to a separate file.
    def handle_get(self, req):
        if req.remote_user.roleid == Role.NO_ADMIN:
            publisher_only = True
        else:
            publisher_only = False


        if not req.system[SystemKeys.WORKBOOK_ARCHIVE_ENABLED]:
            return {'workbooks': [],
                    'item-count': 0,
                    'publisher-only': publisher_only
            }

        filters = self.build_query_filters(req)
        entries = self.do_query(req, filters)
        count = WorkbookEntry.count(filters=filters)

        # lookup caches
        users = ArchiveUserCache(req.envid)
        sites = Site.cache(req.envid)
        projects = Project.cache(req.envid)

        workbooks = []
        for entry in entries:
            data = entry.todict(pretty=True)

            updates = self._build_updates_for_workbook(entry, users)
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
                'item-count': count,
                'publisher-only': publisher_only
        }

    # FIXME: route correctly.
    def service(self, req):
        environ_key = ENVIRON_PREFIX + 'action'
        if environ_key in req.environ:
            action = req.environ[environ_key]
            if action == 'updates/note':
                return self.handle_update_note(req)
            raise exc.HTTPNotFound()

        if req.method == "GET":
            return self.handle_get(req)
        else:
            raise exc.HTTPBadRequest()


class WorkbookData(GenericWSGIApplication):
    """ GET handler for downloading the twb files. """

    def check_permission(self, req, update):
        if req.remote_user.roleid > Role.NO_ADMIN:
            return True
        if req.remote_user.system_user_id == update.workbook.system_user_id:
            return True
        return False

    def service_GET(self, req):
        workbook_name = req.environ[ENVIRON_PREFIX+'name']
        update = WorkbookUpdateEntry.get_by_url(workbook_name, default=None)
        if update is None:
            return exc.HTTPNotFound()

        if not self.check_permission(req, update):
            return exc.HTTPForbidden()

        res = Response()
        res.content_type = 'application/octet-stream'
        res.text = update.twb
        return res

class WorkbookArchive(PalettePage):
    TEMPLATE = 'workbook.mako'
    active = 'workbook-archive'
    archive = True
