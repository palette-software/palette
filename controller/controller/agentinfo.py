import sqlalchemy
from sqlalchemy import Column, String, BigInteger, Integer
from sqlalchemy.schema import ForeignKey
import meta

class AgentYmlEntry(meta.Base):
    __tablename__ = "agent_yml"

    rowkey = Column(Integer, unique=True, nullable=False, primary_key=True)

    agentid = Column(BigInteger, ForeignKey("agent.agentid"))
    key = Column(String)
    value = Column(String)

    def __init__(self, agentid, key, value):
        self.agentid = agentid
        self.key = key
        self.value = value


class AgentPinfoEntry(meta.Base):
    __tablename__ = "agent_pinfo"

    rowkey = Column(Integer, unique=True, nullable=False, primary_key=True)

    agentid = Column(BigInteger, ForeignKey("agent.agentid"))
    key = Column(String)
    value = Column(String)

    def __init__(self, agentid, key, value):
        self.agentid = agentid
        self.key = key
        self.value = value

class AgentVolumesEntry(meta.Base):
    __tablename__ = "agent_volumes"

    rowkey = Column(Integer, unique=True, nullable=False, primary_key=True)

    agentid = Column(BigInteger, ForeignKey("agent.agentid"))

    name = Column(String)
    vol_type = Column(String)
    label = Column(String)
    drive_format = Column(String)

    size = Column(BigInteger)
    free = Column(BigInteger)

    def __init__(self, agentid, name, vol_type, label, drive_format, size, free):
        self.agentid = agentid      # required
        self.name = name            # required
        self.vol_type = vol_type    # required
        self.label = label
        self.drive_format = drive_format
        self.size = size
        self.free = free
