import sqlalchemy
from sqlalchemy import Column, String, BigInteger, Integer, Boolean
from sqlalchemy.schema import ForeignKey
import meta

class AgentYmlEntry(meta.Base):
    __tablename__ = "agent_yml"

    ymlid = Column(Integer, unique=True, nullable=False, primary_key=True)

    agentid = Column(BigInteger, ForeignKey("agent.agentid"))
    key = Column(String)
    value = Column(String)

    def __init__(self, agentid, key, value):
        self.agentid = agentid
        self.key = key
        self.value = value


class AgentInfoEntry(meta.Base):
    __tablename__ = "agent_info"

    infoid = Column(Integer, unique=True, nullable=False, primary_key=True)

    agentid = Column(BigInteger, ForeignKey("agent.agentid"))
    key = Column(String)
    value = Column(String)

class AgentVolumesEntry(meta.Base):
    __tablename__ = "agent_volumes"

    volid = Column(Integer, unique=True, nullable=False, primary_key=True)

    agentid = Column(BigInteger, ForeignKey("agent.agentid"))

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
        size = None; free = None;

        if volume.has_key("name"):
            name = volume['name']

        if volume.has_key("type"):
            vol_type = volume['type']

        if volume.has_key("label"):
            label = volume['label']

        if volume.has_key("drive-format"):
            drive_format = volume['drive-format']

        if volume.has_key("size"):
            size = volume['size']

        if volume.has_key('available-space'):
            free = volume['available-space']

        return AgentVolumesEntry(agentid=agentid, name=name,
            vol_type=vol_type, label=label, drive_format=drive_format,
            size=size, free=free)
