from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from akiri.framework.ext.sqlalchemy import Meta

meta = Meta()
meta.Base = Base
