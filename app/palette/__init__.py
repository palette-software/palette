import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import sessionmaker
import meta

from akiri.framework.api import MainPage

# Set up database connection
db_url = "postgresql://palette:palpass@localhost/paldb"
db_engine = sqlalchemy.create_engine(db_url, echo=False)
#
meta.Base.metadata.create_all(bind=db_engine)
#
Session = sessionmaker(bind=db_engine)

import monitor
import backup
import manage

class DashboardPage(MainPage):
    TEMPLATE = 'dashboard.mako'
