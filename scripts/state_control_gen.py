from akiri.framework.ext.sqlalchemy import meta

import sqlalchemy
from sqlalchemy.orm import sessionmaker, scoped_session

import sys
if len(sys.argv) == 1:
    url = 'postgresql://palette:palpass@localhost/paldb'
elif len(sys.argv) == 2:
    url = sys.argv[1]
else:
    print >> sys.stderr, 'usage: event_control_gen.py [url]'
    sys.exit(1)

url = 'postgresql://palette:palpass@localhost/paldb'
meta.engine = sqlalchemy.create_engine(url, echo=False)
meta.Base.metadata.create_all(bind=meta.engine)
meta.Session = scoped_session(sessionmaker(bind=meta.engine))

envid = 1

########

import json
from collections import OrderedDict

from controller.state_control import StateControl

records = []

for entry in StateControl.get_all_by_keys({}, order_by='stateid'):
    d = OrderedDict()
    d['stateid'] = entry.stateid
    d['state'] = entry.state
    d['text'] = entry.text
    d['allowable_actions'] = entry.allowable_actions
    d['icon'] = entry.icon
    d['color'] = entry.color
    records.append(d)

print json.dumps({'RECORDS':records}, indent=0, separators=(',',':'))        
