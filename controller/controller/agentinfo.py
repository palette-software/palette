from sqlalchemy import Column, String, BigInteger, Integer, Boolean
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm.exc import NoResultFound
from akiri.framework.ext.sqlalchemy import meta

from mixin import BaseDictMixin

class AgentYmlEntry(meta.Base, BaseDictMixin):
    __tablename__ = "agent_yml"

    ymlid = Column(Integer, unique=True, nullable=False, primary_key=True)

    agentid = Column(BigInteger, ForeignKey("agent.agentid"), nullable=False)
    key = Column(String)
    value = Column(String)

class AgentInfoEntry(meta.Base, BaseDictMixin):
    __tablename__ = "agent_info"

    TABLEAU_DATA_DIR_KEY = "tableau-data-dir"
    TABLEAU_DATA_SIZE_KEY = "tableau-data-size"

    infoid = Column(Integer, unique=True, nullable=False, primary_key=True)

    agentid = Column(BigInteger, ForeignKey("agent.agentid"), nullable=False)
    key = Column(String)
    value = Column(String)

class AgentVolumesEntry(meta.Base, BaseDictMixin):
    __tablename__ = "agent_volumes"

    volid = Column(Integer, unique=True, nullable=False, primary_key=True)

    agentid = Column(BigInteger, ForeignKey("agent.agentid"), nullable=False)

    name = Column(String)
    vol_type = Column(String)
    label = Column(String)
    drive_format = Column(String)

    size = Column(BigInteger)
    free = Column(BigInteger)

    system = Column(Boolean)    # The OS/system is installed on this volume

    archive = Column(Boolean)
    archive_limit = Column(BigInteger)

    @classmethod
    def build(cls, agentid, volume):

        name = None; vol_type = None; label = None; drive_format = None;
        archive = False; archive_limit = None; size = None; free = None;

        if volume.has_key("name"):
            name = volume['name']

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
            free = volume['available-space']

        return AgentVolumesEntry(agentid=agentid, name=name,
            vol_type=vol_type, label=label, drive_format=drive_format,
            archive=archive, archive_limit=archive_limit, size=size, free=free)

    @classmethod
    def has_free_space(cls, agentid, min_needed):
        """Searches for a volume on the agent that has
        the requested disk space for archiving.  If found, returns
        the volume entry.  If not, returns False."""

        try:
            return meta.Session.query(AgentVolumesEntry).\
                    filter(AgentVolumesEntry.agentid == agentid).\
                    filter(AgentVolumesEntry.vol_type == "Fixed").\
                    filter(AgentVolumesEntry.archive == True).\
                    filter(AgentVolumesEntry.free >= min_needed).\
                    filter(AgentVolumesEntry.size - AgentVolumesEntry.free + \
                            min_needed < AgentVolumesEntry.archive_limit).\
                    one()   # for now, choosen any one - no particular order.

        except NoResultFound, e:
            return False
