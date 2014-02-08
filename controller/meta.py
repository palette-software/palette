from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

import platform
# fixme: move to .ini config file
if platform.system() == 'Windows':
    # Windows with Tableau uses port 8060
    url = "postgresql://palette:palpass@localhost:8060/paldb"
else:
    url = "postgresql://palette:palpass@localhost/paldb"

engine = None
