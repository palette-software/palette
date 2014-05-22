from sqlalchemy import Column, String, Integer, Boolean, Unicode
from sqlalchemy.orm.exc import NoResultFound

from akiri.framework.ext.sqlalchemy import meta

from rbac import User

class UserProfile(User):
    """
    Profile information is added to the 'users' table.
    """
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    tableau_username = Column(String)
    gmt = Column(String)
    timezone_offset_minutes = Column(Integer)
    password = Column('password', Unicode(160))

    @classmethod
    def get_by_name(cls, name):
        try:
            entry = meta.Session.query(UserProfile).\
                            filter(UserProfile.name == name).one()
        except NoResultFound, e:
            entry = None
        return entry
