import re

from sqlalchemy import Column, String, Integer, BigInteger, DateTime
from sqlalchemy import func

import akiri.framework.sqlalchemy as meta

from mixin import BaseMixin
from system import SystemKeys

def list_re(arg):
    _ = []
    arg = arg.replace(',', ' ')
    for token in arg.split(' '):
        if token:
            _.append(re.compile(token))
    return _

def match_re(patterns, arg):
    for pattern in patterns:
        if pattern.match(arg):
            return True

    return False

class HttpControl(meta.Base, BaseMixin):
    __tablename__ = "http_control"

    hcid = Column(BigInteger, unique=True, nullable=False,
                  autoincrement=True, primary_key=True)

    status = Column(BigInteger, unique=True, nullable=False)
    level = Column(Integer, nullable=False, default=1)
    excludes = Column(String)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(),
                               onupdate=func.current_timestamp())

    exclude_str = r'.+(\.(png|pdf|csv|bmp|emf|mdb|xml)(\Z|\?)|' + \
                                 r'format=(png|pdf|csv|bmp|emf|mdb|xml))'
    defaults = [{'status':404, 'excludes': exclude_str},
                {'status':500, 'excludes': exclude_str}]

    @classmethod
    def all(cls):
        return meta.Session.query(HttpControl).\
            filter(HttpControl.level > 0).\
            all()

class HttpControlData(object):

    def __init__(self, server):
        self.server = server

        self.status_excludes = {}
        for entry in HttpControl.all():
            if entry.excludes:
                excludes = list_re(entry.excludes)
                if excludes:
                    self.status_excludes[entry.status] = excludes

        self.load_excludes = []
        arg = server.system[SystemKeys.HTTP_LOAD_RE]
        if arg:
            self.load_excludes = list_re(arg)

    def status_exclude(self, status, url):
        if status not in self.status_excludes:
            return False
        excludes = self.status_excludes[status]
        return match_re(excludes, url)

    def load_exclude(self, url):
        return match_re(self.load_excludes, url)
