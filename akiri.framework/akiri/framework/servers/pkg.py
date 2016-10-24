#!/usr/bin/env python
"""WSGI application to control 'apt'."""

# Based on apt_check.py from update-notifier (no license)
# see /usr/lib/update-notifier/apt-check
# NOTE: this module uses the higher-level 'apt' instead of 'apt_pkg'
from __future__ import absolute_import
import apt
from collections import OrderedDict
from webob import exc

# FIXME: use gettext for multilingual support
from .. import GenericWSGI
from ..route import Router
from ..util import str2bool

# FIXME: add support for 'installed'
# FIXME: handle security updates.

# FIXME: use req.params_getbool
def _getbool(req, name, default=None):
    """Return a POST parameter as a boolean value - or default if not found."""
    if name in req.POST:
        return str2bool(req.POST[name])
    else:
        return default

class BasePkgApp(GenericWSGI):
    """Base class for all handler apps in this module."""

    def preprocess(self, req, cache):
        """
        (Abstract) method to be run after cache is set up, but before
        and handling of the request takes place.
        """
        pass

    def service(self, req):
        """Service the request by delegating to do_one/do_all."""
        cache = apt.Cache(memonly=True)
        self.preprocess(req, cache)

        if 'pkgname' in req.environ:
            pkgname = req.environ['pkgname']
            if not pkgname in cache:
                raise exc.HTTPNotFound()
            pkg = cache[pkgname]
            return self.do_one(pkg, req, cache)
        else:
            return self.do_all(req, cache)

    def do_one(self, pkg, req, cache):
        """Service a particular package"""
        # pylint: disable=unused-argument
        # pylint: disable=no-self-use
        raise exc.HTTPNotImplemented()

    def do_all(self, req, cache):
        """Service all packages"""
        # pylint: disable=unused-argument
        # pylint: disable=no-self-use
        raise exc.HTTPNotImplemented()

    def todict(self, pkg):
        """Convert a package to a dict usable by JSON."""
        # pylint: disable=no-self-use
        data = OrderedDict({})
        data['name'] = pkg.name
        data['id'] = pkg.id
        data['fullname'] = pkg.fullname
        data['section'] = pkg.section

        description = None
        if pkg.candidate:
            data['candidate'] = pkg.candidate.version
            description = pkg.candidate.description
        if pkg.installed:
            data['installed'] = pkg.installed.version
            if description:
                description = pkg.installed.description
        data['essential'] = pkg.essential
        if description:
            data['description'] = description
        return data


class AllPkgApp(BasePkgApp):
    """Displays information about all packages regardless of upgrade status."""

    def preprocess(self, req, cache):
        if req.method != 'GET':
            raise exc.HTTPMethodNotAllowed()

        # FIXME: only call if running at EUID == 0 (root)
        # cache.update()
        #cache.open(None)

    def do_one(self, pkg, req, cache):
        return {'package': self.todict(pkg)}

    def do_all(self, req, cache):
        pkgs = []
        for pkg in cache:
            pkgs.append(self.todict(pkg))
        return {'packages': pkgs}


class InstallPkgApp(BasePkgApp):
    """Displays information about all packages regardless of upgrade status."""

    def preprocess(self, req, cache):
        if req.method != 'GET':
            raise exc.HTTPMethodNotAllowed()

    def do_one(self, pkg, req, cache):
        if not pkg.is_installed:
            raise exc.HTTPNotFound()
        data = self.todict(pkg)
        data['files'] = pkg.installed_files
        return {'package': data}

    def do_all(self, req, cache):
        pkgs = []
        for pkg in cache:
            if pkg.is_installed:
                pkgs.append(self.todict(pkg))
        return {'packages': pkgs}

class UpdatePkgApp(BasePkgApp):
    """WSGI application for handling packages that can be updated and for
    doing updates via POST requests."""

    def _build_update_list(self, cache):
        """Return the list of packages that may be updated."""
        updates = []
        for pkg in cache:
            # skip packages that are not marked upgraded/installed
            if not pkg.is_upgradable:
                continue

            # NOTE: this script doesn't participate in phasing, which is
            # why the returned list may be a superset of what other
            # update managers show.

            data = self.todict(pkg)
            updates.append(data)
        return updates

    def do_all(self, req, cache):
        if req.method == 'GET':
            return {'updates': self._build_update_list(cache)}
        if req.method != 'POST':
            raise exc.HTTPMethodNotAllowed()
        if not 'action' in req.POST or req.POST['action'] != 'install':
            raise exc.HTTPBadRequest()
        if 'dist_upgrade' in req.POST:
            dist_upgrade = str2bool(req.POST['dist_upgrade'])
        else:
            # This value is different from the default upgrade parameter,
            # but prevents breaking a package with new dependencies.
            dist_upgrade = True
        cache.upgrade(dist_upgrade=dist_upgrade)
        install_count = cache.install_count
        cache.commit()
        return {'status': 'OK', 'install-count': install_count}

    def do_one(self, pkg, req, cache):
        if not pkg.is_upgradable:
            # FIXME: allow reinstall?
            raise exc.HTTPNotFound()

        if req.method == 'GET':
            return {'update': self.todict(pkg)}
        if req.method != 'POST':
            raise exc.HTTPMethodNotAllowed()

        auto_fix = _getbool(req, 'auto_fix', default=True)
        auto_inst = _getbool(req, 'auto_inst', default=True)
        from_user = _getbool(req, 'from_user', default=True)

        pkg.mark_install(auto_fix=auto_fix,
                         auto_inst=auto_inst,
                         from_user=from_user)
        cache.commit()
        return {'status': 'OK'}


class PkgApp(Router):
    """Main package application - essentially just a router for the other
    applications in this module."""
    def __init__(self):
        super(PkgApp, self).__init__()
        self.add_redirect(r'/\Z', '/install')
        self.add_route(r'/update(/(?P<pkgname>[^\s/]+))?\Z', UpdatePkgApp())
        self.add_route(r'/all(/(?P<pkgname>[^\s/]+))?\Z', AllPkgApp())
        self.add_route(r'/install(/(?P<pkgname>[^\s/]+))?\Z', InstallPkgApp())

# pylint: disable=invalid-name
application = PkgApp()
