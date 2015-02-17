from sqlalchemy import Column, Integer, BigInteger, String
from sqlalchemy.orm.exc import NoResultFound

import akiri.framework.sqlalchemy as meta

from mixin import BaseMixin

class DataSourceTypes(meta.Base, BaseMixin):
    __tablename__ = "data_source_types"

    datastid = Column(BigInteger, unique=True, nullable=False,
                                  autoincrement=True, primary_key=True)

    data_source = Column(String, unique=True)
    standard_port = Column(Integer)
    standard_host = Column(String)

    driver_version = Column(String)
    driver_install_location = Column(String)
    dbclass = Column(String)

    @classmethod
    def get_data_source_types_entry(cls, data_source):
        try:
            entry = meta.Session.query(DataSourceTypes).\
                filter(DataSourceTypes.data_source == data_source).one()
        except NoResultFound:
            return None

        return entry

    defaults_filename = 'data_source_types.json'
