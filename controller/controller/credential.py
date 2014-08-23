from sqlalchemy import Column, BigInteger, Integer, Boolean, String, DateTime
from sqlalchemy import func, UniqueConstraint
from sqlalchemy.schema import ForeignKey

from akiri.framework.ext.sqlalchemy import meta

from mixin import BaseMixin, BaseDictMixin
from cache import TableauCacheManager
from util import odbc2dt

from passwd import aes_encrypt, aes_decrypt

class CredentialEntry(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = "credentials"

    credid = Column(BigInteger, unique=True, nullable=False,
                    autoincrement=True, primary_key=True)
    envid = Column(Integer, ForeignKey("environment.envid"), nullable=False)
    key = Column(String, nullable=False)
    user = Column(String, nullable=False)
    embedded = Column(String)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(),
                               onupdate=func.current_timestamp())

    __table_args__ = (UniqueConstraint('envid', 'key'),)

    def getpasswd(self):
        if not self.embedded:
            return self.embedded
        return aes_decrypt(self.embedded)

    def setpasswd(self, cleartext):
        self.embedded = aes_encrypt(cleartext)

class CredentialManager(Manager):

    def get(self, key, **kwargs):
        return CredentialEntry.\
            get_unique_by_envid_key(envid, 'key', key, **kwargs)
