from sqlalchemy import Column, String, Integer, Boolean, Unicode
from sqlalchemy.orm.exc import NoResultFound

from akiri.framework.ext.sqlalchemy import meta

from rbac import User
from passwd import tableau_hash

class UserProfile(User):
    """
    Profile information is added to the 'users' table.
    """
    friendly_name = Column(String)
    email = Column(String)
    hashed_password = Column(String)
    salt = Column(String)

    @classmethod
    def get_by_name(cls, name):
        try:
            entry = meta.Session.query(UserProfile).\
                            filter(UserProfile.name == name).one()
        except NoResultFound, e:
            entry = None
        return entry

    @classmethod
    def verify(cls, name, password):
        entry = cls.get_by_name(name)
        if not entry:
            return False
        return entry.hashed_password == tableau_hash(password, entry.salt)

    @classmethod
    def populate(cls):
        session = meta.Session()
        entry = session.query(UserProfile).first()
        if entry:
            return
        entry = UserProfile(name='palette', friendly_name='Palette SuperAdmin',
                            email=None, salt='',
                            hashed_password=tableau_hash('tableau2014',''))
        session.add(entry)
        session.commit()
