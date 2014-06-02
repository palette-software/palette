from akiri.framework.ext.sqlalchemy import meta

from sqlalchemy import Column, Integer, BigInteger, String
from sqlalchemy.schema import ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.exc import NoResultFound

from mixin import BaseMixin

from UserDict import IterableUserDict
class Dict(IterableUserDict):

    def __setitem__(self, key, value):
        if not hasattr(value, "__getitem__"):
            raise TypeError('value is not a list.')
        IterableUserDict.__setitem__(self, key, value)

    def add(self, key, values):
        for value in values:
            if not value in self[key]:
                self[key].append(value)
                self.__modified__ = True
            if value in self:
                self.add(key, self[value])

    def recursive_join(self):
        while True:
            self.__modified__ = False
            for key in self:
                for value in self[key]:
                    if value in self:
                        self.add(key, self[value])
            if not self.__modified__:
                return

# MANY-TO-MANY relationships

user_roles = Table('user_roles', meta.Base.metadata,
                   Column('userid', BigInteger, ForeignKey('users.userid'),
                          primary_key=True),
                   Column('roleid', BigInteger, ForeignKey('roles.roleid'),
                          primary_key=True)
)

role_roles = Table('role_roles', meta.Base.metadata,
                   Column('childid', BigInteger, ForeignKey('roles.roleid'),
                          primary_key=True),
                   Column('parentid', BigInteger, ForeignKey('roles.roleid'),
                          primary_key=True)
)

role_permissions = Table('role_permissions', meta.Base.metadata,
                         Column('roleid', BigInteger,
                                ForeignKey('roles.roleid'),
                                primary_key=True),
                         Column('permid', BigInteger,
                                ForeignKey('permissions.permid'),
                                primary_key=True)
)

# NOTE: no classes have explicty constructors, instead we use the
# keyword-based constructors unless some other preparation is required.

# http://docs.sqlalchemy.org/en/rel_0_9/orm/relationships.html#self-referential-many-to-many-relationship
class Role(meta.Base, BaseMixin):
    __tablename__ = 'roles'

    roleid = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)

    # this relationship should not be used directly
    # use addrole() instead.
    _parents = relationship('Role',  backref='_children', lazy='dynamic',
                          secondary=role_roles, join_depth=2,
                          primaryjoin=roleid==role_roles.c.childid,
                          secondaryjoin=roleid==role_roles.c.parentid)

    # intentionally no 'backref' here - confusing semantics.
    permissions = relationship('Permission',
                               secondary=role_permissions, join_depth=2)

    @classmethod
    def map2(cls):
        sql = \
            "SELECT roles1.name as childname, roles2.name as parentname " +\
            "FROM roles as roles1 " +\
            "JOIN role_roles ON roles1.roleid=role_roles.childid " +\
            "JOIN roles as roles2 ON role_roles.parentid=roles2.roleid"

        d = Dict()
        for childname, parentname in meta.engine.execute(sql):
            if childname not in d:
                d[childname] = []
            d[childname].append(parentname)

        d.recursive_join()
        return d

    def _roles(self):
        rolemap = Role.map2()
        if self.name not in rolemap:
            return []
        names = rolemap[self.name]
        return meta.Session.query(Role).filter(Role.name.in_(names))

    def __getattr__(self, name):
        if name == 'roles':
            return self._roles()
        raise AttributeError(name)

    def addrole(self, parent):
        if self in parent._roles() :
            raise ValueError('Invalid ROLE hierarchy')
        self._parents.append(parent)

    defaults = [{'roleid':0, 'name':"No Admin"},
                {'roleid':1, 'name':"Read-Only Admin"},
                {'roleid':2, 'name':"Manager Admin"},
                {'roleid':3, 'name':"Super Admin"}]

class Permission(meta.Base):
    __tablename__ = 'permissions'

    permid = Column(BigInteger, unique=True, nullable=False, \
                        autoincrement=True, primary_key=True)
    name = Column(String, unique=True, nullable=False)


class User(meta.Base):
    __tablename__ = 'users'

    userid = Column(BigInteger, unique=True, nullable=False, \
                        autoincrement=True, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    # immediate roles i.e. roles not inherited.
    _roles = relationship('Role', backref='users',
                          secondary=user_roles, join_depth=2)

    def addrole(self, role):
        """ Add a user to a role - better name than '_roles'."""
        self._roles.append(role)

    @classmethod
    def get_by_name(cls, name):
        try:
            entry = meta.Session.query(User).filter(User.name == name).one()
        except NoResultFound, e:
            entry = None
        return entry

    def getroles(self):
        rolemap = Role.map2()
        d = {}
        for role in self._roles:
            d[role.name] = role.name
            if role.name in rolemap:
                for parent in rolemap[role.name]:
                    d[parent.name] = parent.name
        return meta.Session.query(Role).filter(Role.name.in_(d.values()))

    def _permissions(self):
        session = meta.Session()
        ids = [role.roleid for role in self.roles]
        q = meta.Session.query(Permission).join(role_permissions, Role)
        return q.filter(Role.roleid.in_(ids)).all()

    def __getattr__(self, name):
        if name == 'roles':
            return self.getroles()
        if name == 'permissions':
            return self._permissions()
        raise AttributeError(name)
