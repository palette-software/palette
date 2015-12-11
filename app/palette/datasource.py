""" The datasource archive. """

from collections import OrderedDict
from webob import exc, Response

from akiri.framework import GenericWSGIApplication, ENVIRON_PREFIX
import akiri.framework.sqlalchemy as meta

from controller.datasources import DataSourceEntry, DataSourceUpdateEntry
from controller.profile import UserProfile, Role
from controller.sites import Site
from controller.projects import Project
from controller.system import SystemKeys

from .archive import ArchiveApplication, ArchiveUserCache
from .option import DictOption
from .page import PalettePage
from .rest import required_parameters, required_role

class DatasourceShow(DictOption):
    """Options to show all datasources or only for the current user."""
    NAME = 'show-dropdown'
    ALL = 0
    MINE = 1

    @classmethod
    def items(cls):
        return OrderedDict({
            cls.ALL: 'All Data Sources',
            cls.MINE: 'My Data Sources'})

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
            cls.DATASOURCE: 'Data Source',
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


class DatasourceApplication(ArchiveApplication):
    """ The REST application for the datasource archive page. """

    def show_options(self, req):
        valueid = req.params_getint('show', DatasourceShow.ALL)
        return DatasourceShow(valueid).default()

    def sort_options(self, req):
        valueid = req.params_getint('sort', DatasourceSort.DATASOURCE)
        return DatasourceSort(valueid, req).default()

    # FIXME: covert to /datasource/<id>/note or /datasource/note/<id>
    # GET doesn't have a ready meaning.
    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('id', 'value')
    def handle_update_note(self, req):
        update = DataSourceUpdateEntry.get_by_id(req.POST['id'])
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
            data = update.todict(pretty=True, exclude='tds')
            data['username'] = users[update.system_user_id]
            if 'url' in data and data['url']:
                # FIXME: make this configurable
                data['url'] = '/data/datasource-archive/' + data['url']
            updates.append(data)
        return updates

    def handle_get(self, req):
        # pylint: disable=too-many-locals
        enabled = req.system[SystemKeys.DATASOURCE_RETAIN_COUNT]

        if req.remote_user.roleid == Role.NO_ADMIN:
            publisher_only = True
        else:
            publisher_only = False

        # total count for this environment
        # FIXME: too heavy weight for setting populated
        if DataSourceEntry.count(filters={'envid':req.envid}) > 0:
            populated = True
        else:
            populated = False

        if populated and enabled:
            filters = self.build_query_filters(req)
            entries = self.do_query(req, filters)
            count = DataSourceEntry.count(filters=filters)
        else:
            entries = []
            count = 0

        # lookup caches
        users = ArchiveUserCache(req.envid)
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

        return {'datasources': datasources,
                'config': self.build_config(req, sites, projects),
                'item-count': count,
                'populated': populated,
                'enabled': enabled,
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


class DatasourceData(GenericWSGIApplication):
    """ GET handler for downloading the tds files. """

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

        res = Response()
        res.content_type = 'application/octet-stream'
        res.text = update.tds
        return res

class DatasourceArchive(PalettePage):
    TEMPLATE = 'datasource.mako'
    active = 'datasource-archive'
    archive = True
