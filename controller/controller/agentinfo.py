from sqlalchemy import Column, String, BigInteger, Integer, Boolean
from sqlalchemy.schema import ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.exc import NoResultFound
from akiri.framework.ext.sqlalchemy import meta

from util import sizestr
from mixin import BaseDictMixin

# FIXME: move these classes to agent.py
class AgentYmlEntry(meta.Base, BaseDictMixin):
    __tablename__ = "agent_yml"

    ymlid = Column(Integer, unique=True, nullable=False, primary_key=True)

    agentid = Column(BigInteger, ForeignKey("agent.agentid"), nullable=False)
    key = Column(String)
    value = Column(String)

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

    system = Column(Boolean)    # The OS/system is installed on this volume

    archive = Column(Boolean)
    archive_limit = Column(BigInteger)

    primary_data_loc = Column(Boolean)
    active = Column(Boolean)

    agent = relationship('Agent', backref='volumes')
    UniqueConstraint('agentid', 'name')

    def todict(self, pretty=False):
        d = super(AgentVolumesEntry, self).todict(pretty=pretty)
        if not self.size is None and not self.available_space is None:
            d['used'] = self.size - self.available_space
        if not pretty:
            return d
        if 'size' in d: d['size-readable'] = sizestr(d['size'])
        if 'available-space' in d:
            d['available-readable'] = sizestr(d['available-space'])
        if 'used' in d: d['used-readable'] = sizestr(d['used'])
        return d

    @classmethod
    def build(cls, agentid, volume):

        name = None; path = None; vol_type = None; label = None;
        drive_format = None; archive = False; archive_limit = None;
        size = None; available_space = None;

        if volume.has_key("name"):
            name = volume['name'].upper()

        if volume.has_key('path'):
            path = volume['path']

        if volume.has_key("size"):
            size = volume['size']

        if volume.has_key("type"):
            vol_type = volume['type']
            if vol_type == 'Fixed':
                archive = True
                if size:
                    archive_limit = size    # fixme: can't use whole disk

        if volume.has_key("label"):
            label = volume['label']

        if volume.has_key("drive-format"):
            drive_format = volume['drive-format']
        if volume.has_key('available-space'):
            available_space = volume['available-space']

        return AgentVolumesEntry(agentid=agentid, name=name, path=path,
            vol_type=vol_type, label=label, drive_format=drive_format,
            archive=archive, archive_limit=archive_limit, size=size, 
            available_space=available_space, primary_data_loc=False,
                                                            active=True)

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

        except NoResultFound, e:
            return False

    @classmethod
    def get_vol_entry_by_volid(cls, volid):
        try:
            return meta.Session.query(AgentVolumesEntry).\
                filter(AgentVolumesEntry.volid == volid).\
                one()
        except NoResultFound, e:
            return None
    get_by_id = get_vol_entry_by_volid

    @classmethod
    def get_vol_entries_by_agentid(cls, agentid):
        try:
            return meta.Session.query(AgentVolumesEntry).\
                filter(AgentVolumesEntry.agentid == agentid).\
                all()
        except NoResultFound, e:
            return None
