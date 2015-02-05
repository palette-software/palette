from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Boolean
from sqlalchemy import func
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from passwd import tableau_hash
from mixin import BaseMixin, BaseDictMixin

class UserProfile(meta.Base, BaseMixin, BaseDictMixin):
    """
    Profile information is added to the 'users' table.
    """
    PALETTE_DEFAULT_NAME = 'palette'
    PALETTE_DEFAULT_FRIENDLY_NAME = 'Palette Install User'
    PALETTE_DEFAULT_PASSWORD = 'Tableau2014!'

    __tablename__ = 'users'
    userid = Column(BigInteger, unique=True, nullable=False, \
                        autoincrement=True, primary_key=True)
    envid = Column(BigInteger, ForeignKey("environment.envid"), nullable=False)
    active = Column(Boolean, default=True)
    name = Column(String, unique=True, nullable=False)
    friendly_name = Column(String)
    email = Column(String)
    email_level = Column(Integer, default=1)
    hashed_password = Column(String)
    salt = Column(String)
    roleid = Column(BigInteger, ForeignKey("roles.roleid"), default=0)
    system_user_id = Column(Integer, unique=True)
    login_at = Column(DateTime)
    licensing_role_id = Column(Integer)
    user_admin_level = Column(Integer)
    system_admin_level = Column(Integer)
    publisher = Column(Boolean)
    system_created_at = Column(DateTime)
    timestamp = Column(DateTime) # last active time (in Palette)
    modification_time = Column(DateTime, server_default=func.now(),
                               onupdate=func.current_timestamp())

    role = relationship("Role")

    def __unicode__(self):
        if self.friendly_name:
            return unicode(self.friendly_name)
        return unicode(self.name)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def display_name(self):
        return unicode(self)

    def display_role(self):
        # pylint: disable=no-member
        if self.publisher:
            if self.roleid == Role.NO_ADMIN:
                return u'Publisher'
            return u'Publisher & ' + self.role.name
        else:
            return self.role.name

    @classmethod
    def get(cls, envid, userid):
        filters = {'envid':envid, 'userid':userid}
        return cls.get_unique_by_keys(filters, default=None)

    @classmethod
    def get_by_system_user_id(cls, envid, system_user_id):
        filters = {'envid':envid, 'system_user_id':system_user_id}
        return cls.get_unique_by_keys(filters, default=None)

    @classmethod
    def get_by_name(cls, envid, name):
        try:
            query = meta.Session.query(UserProfile).\
                    filter(UserProfile.envid == envid).\
                    filter(func.lower(UserProfile.name) == name.lower())
            entry = query.one()
        except NoResultFound:
            entry = None
        return entry

    @classmethod
    def verify(cls, envid, name, password):
        entry = cls.get_by_name(envid, name)
        if not entry:
            return False
        return entry.hashed_password == tableau_hash(password, entry.salt)

    defaults = [{'userid':0, 'envid':1, 'name':PALETTE_DEFAULT_NAME,
                 'friendly_name':PALETTE_DEFAULT_FRIENDLY_NAME,
                 'email':None, 'salt':'', 'roleid':3, # SUPER_ADMIN
                 'system_user_id':0}]

class Role(meta.Base, BaseMixin):
    __tablename__ = 'roles'

    NO_ADMIN = 0
    READONLY_ADMIN = 1
    MANAGER_ADMIN = 2
    SUPER_ADMIN = 3

    roleid = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)

    @classmethod
    def get_by_name(cls, name):
        try:
            entry = meta.Session.query(Role).filter(Role.name == name).one()
        except NoResultFound:
            entry = None
        return entry

    @classmethod
    def get_by_roleid(cls, roleid):
        try:
            entry = meta.Session.query(Role).filter(Role.roleid == roleid).one()
        except NoResultFound:
            entry = None
        return entry

    defaults = [{'roleid':NO_ADMIN, 'name':"None"},
                {'roleid':READONLY_ADMIN, 'name':"Read-Only Admin"},
                {'roleid':MANAGER_ADMIN, 'name':"Manager Admin"},
                {'roleid':SUPER_ADMIN, 'name':"Super Admin"}]

class License(object):
    UNLICENSED = 3
    INTERACTOR = 2
    VIEWER = 1

    @classmethod
    def str(cls, val):
        if val == License.UNLICENSED:
            return 'Unlicensed'
        if val == License.INTERACTOR:
            return 'Interactor'
        if val == License.VIEWER:
            return 'Viewer'
        return 'Unknown('+str(val)+')'

class Publisher(object):
    DENY = 0
    IMPLICIT = 1
    GRANTED = 2

    @classmethod
    def str(cls, val):
        if val == Publisher.DENY:
            return 'Deny'
        if val == Publisher.IMPLICIT:
            return 'Allow (Implicit)'
        if val == Publisher.GRANTED:
            return 'Allow (Granted)'
        return 'Unknown('+str(val)+')'

class Admin(object):

    @classmethod
    def str(cls, user, system):
        if user == 5 and system == 0:
            return 'Site Admin'
        if user == 0 and system == 10:
            return 'System Admin'
        if user == 0 and system == 0:
            return 'No Admin'
        return 'Unknown('+str(user)+','+str(system)+')'
