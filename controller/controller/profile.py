import sqlalchemy

import meta

from sqlalchemy import Column, String, Boolean, Unicode
from sqlalchemy.orm.exc import NoResultFound

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
    salt = Column(Unicode(24))
    password = Column('password', Unicode(160))

    @classmethod
    def get_by_name(cls, name):
        try:
            entry = meta.Session.query(UserProfile).\
                            filter(UserProfile.name == name).one()
        except NoResultFound, e:
            entry = None
        return entry

