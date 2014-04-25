import sqlalchemy
from sqlalchemy import Column, String, BigInteger
from sqlalchemy.schema import ForeignKey
import meta

class AgentInfoEntry(meta.Base):
    __tablename__ = "agent_info"

    agentid = Column(BigInteger, ForeignKey("agent.agentid"),
                                        primary_key=True, unique=True)
    workgroup_yml = Column(String)
    pinfo = Column(String)

    def __init__(self, agentid, workgroup_yml, pinfo):
        self.agentid = agentid
        self.workgroup_yml = workgroup_yml
        self.pinfo = pinfo
