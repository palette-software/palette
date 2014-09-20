import os

from sqlalchemy import Column, String, BigInteger, Integer, Boolean, asc
from sqlalchemy import not_, UniqueConstraint
from sqlalchemy.schema import ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.exc import NoResultFound

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from util import sizestr
from mixin import BaseMixin, BaseDictMixin

# FIXME: this class needs to be in another module since YML is not treated
# like the system table, i.e. it's tied to an environment, not the agent.
class AgentYmlEntry(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = "agent_yml"

    ymlid = Column(Integer, unique=True, nullable=False, primary_key=True)
    envid = Column(BigInteger, ForeignKey("environment.envid"),
                   primary_key=True)
    key = Column(String)
    value = Column(String)

    __table_args__ = (UniqueConstraint('envid', 'key'),)

    @classmethod
    def entry(cls, envid, key, **kwargs):
        filters = {'envid':envid, 'key':key}
        return cls.get_unique_by_keys(filters, **kwargs)

    @classmethod
    def get(cls, envid, key, **kwargs):
        if 'default' in kwargs:
            default = kwargs['default']
            have_default = True
            del kwargs['default']
        else:
            have_default = False

        if kwargs:
            raise ValueError("Invalid kwargs")

        try:
            entry = cls.entry(envid, key, **kwargs)
        except ValueError, ex:
            if have_default:
                return default
            else:
                raise ex
        return entry.value

    @classmethod
    def sync(cls, envid, yml):
        """
        Replace all YML entries for a particular environment with passed list.
        The new contents are then returned as a dictionary.
        """
        session = meta.Session()

        d = {}
        # This is the first line ('---')
        for line in yml.strip().split('\n')[1:]:
            key, value = line.split(":", 1)
            value = value.strip()

            entry = cls.entry(envid, key, default=None)
            if entry is None:
                entry = AgentYmlEntry(envid=envid, key=key)
            entry.value = value
            session.add(entry)
            d[key] = value

        session.query(AgentYmlEntry).\
            filter(not_(AgentYmlEntry.key.in_(d.keys()))).\
            delete(synchronize_session='fetch')

        session.commit()
        return d


# FIXME: move these classes to agent.py
class AgentVolumesEntry(meta.Base, BaseDictMixin):
    __tablename__ = "agent_volumes"

    volid = Column(Integer, unique=True, nullable=False, primary_key=True)

    agentid = Column(BigInteger, ForeignKey("agent.agentid"), nullable=False)

    name = Column(String)
    path = Column(String)
    vol_type = Column(String)
    label = Column(String)
    drive_format = Column(String)

    size = Column(BigInteger)
    available_space = Column(BigInteger)

    # Last notification about disk low or high watermark:
    #  "r" (red), "y" (yellow) or null.
    watermark_notified_color = Column(String(1))

    system = Column(Boolean)    # The OS/system is installed on this volume

    archive = Column(Boolean)
    archive_limit = Column(BigInteger)

    active = Column(Boolean)

    agent = relationship('Agent',
                         backref=backref('volumes',
                                         order_by='AgentVolumesEntry.name')
                         )
    UniqueConstraint('agentid', 'name')

    def todict(self, pretty=False, exclude=None):
        d = super(AgentVolumesEntry, self).todict(pretty=pretty)
        if not self.size is None and not self.available_space is None:
            d['used'] = self.size - self.available_space
        if not pretty:
            return d
        if 'size' in d:
            d['size-readable'] = sizestr(d['size'])
        if 'available-space' in d:
            d['available-readable'] = sizestr(d['available-space'])
        if 'used' in d:
            d['used-readable'] = sizestr(d['used'])
        return d

    @classmethod
    def build(cls, agent, volume, install_data_dir):
        # pylint: disable=multiple-statements
        name = None; path = None; vol_type = None; label = None
        drive_format = None; archive = False; archive_limit = None
        size = None; available_space = None

        if volume.has_key("name"):
            name = volume['name']
            if agent.iswin:
                name = volume['name'].upper()

        if volume.has_key('path'):
            path = volume['path']

        if volume.has_key("size"):
            size = volume['size']

        if volume.has_key("type"):
            vol_type = volume['type']
            if agent.iswin and vol_type == 'Fixed':
                archive = True
                path = install_data_dir
            elif not agent.iswin and volume['type'][:7] == '/dev/sd' and \
                name != None and \
                        os.path.commonprefix([agent.data_dir, name]) == name:
                # The data-dir is on the entry's mount point so it is
                # the "archive" entry.
                archive = True
                path = install_data_dir

        if archive == True:
            if size:
                archive_limit = size    # fixme: can't use whole disk

        if volume.has_key("label"):
            label = volume['label']

        if volume.has_key("drive-format"):
            drive_format = volume['drive-format']

        if volume.has_key('available-space'):
            available_space = volume['available-space']

        return AgentVolumesEntry(agentid=agent.agentid, name=name, path=path,
            vol_type=vol_type, label=label, drive_format=drive_format,
            archive=archive, archive_limit=archive_limit, size=size,
            available_space=available_space, active=True)

    @classmethod
    def has_available_space(cls, agentid, min_needed):
        """Searches for a volume on the agent that has
        the requested disk space for archiving.  If found, returns
        the volume entry.  If not, returns False."""

        try:
            return meta.Session.query(AgentVolumesEntry).\
                    filter(AgentVolumesEntry.agentid == agentid).\
                    filter(AgentVolumesEntry.vol_type == "Fixed").\
                    filter(AgentVolumesEntry.archive == True).\
                    filter(AgentVolumesEntry.active == True).\
                    filter(AgentVolumesEntry.available_space >= min_needed).\
                    filter(AgentVolumesEntry.size - \
                                AgentVolumesEntry.available_space +
                                min_needed < AgentVolumesEntry.archive_limit).\
                    one()   # for now, choosen any one - no particular order.

        except NoResultFound:
            return False

    @classmethod
    def get_vol_entry_by_agentid_vol_name(cls, agentid, vol_name):
        # pylint: disable=invalid-name
        try:
            return meta.Session.query(AgentVolumesEntry).\
                filter(AgentVolumesEntry.agentid == agentid).\
                filter(AgentVolumesEntry.name == vol_name).\
                one()
        except NoResultFound:
            return None

    @classmethod
    def get_vol_entry_by_volid(cls, volid):
        # pylint: disable=invalid-name
        try:
            return meta.Session.query(AgentVolumesEntry).\
                filter(AgentVolumesEntry.volid == volid).\
                one()
        except NoResultFound:
            return None
    get_by_id = get_vol_entry_by_volid

    @classmethod
    def get_vol_entry_with_agent_by_volid(cls, volid):
        # pylint: disable=invalid-name
        try:
            return meta.Session.query(AgentVolumesEntry).\
                filter(AgentVolumesEntry.volid == volid).\
                join('agent').\
                filter_by(agentid=AgentVolumesEntry.agentid).\
                one()
        except NoResultFound:
            return None

    @classmethod
    def get_vol_archive_entries_by_agentid(cls, agentid):
        # pylint: disable=invalid-name
        return meta.Session.query(AgentVolumesEntry).\
            filter(AgentVolumesEntry.archive == True).\
            filter(AgentVolumesEntry.agentid == agentid).\
            order_by(AgentVolumesEntry.name.desc()).\
            all()

    @classmethod
    def get_archives_by_envid(cls, envid):
        return meta.Session.query(AgentVolumesEntry).\
            filter_by(archive=True).\
            join('agent').\
            filter_by(envid=envid).\
            order_by(asc('agent.display_order'), asc('name')).\
            all()
