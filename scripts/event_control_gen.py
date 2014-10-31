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

meta.engine = sqlalchemy.create_engine(url, echo=False)
meta.Base.metadata.create_all(bind=meta.engine)
meta.Session = scoped_session(sessionmaker(bind=meta.engine))

envid = 1

########

import json
from collections import OrderedDict

from controller.event_control import EventControl

records = []

for entry in EventControl.get_all_by_keys({}, order_by='eventid'):
    d = OrderedDict()
    d['eventid'] = entry.eventid
    d['key'] = entry.key
    d['level'] = entry.level
    d['send_email'] = entry.send_email and 't' or 'f'
    d['subject'] = entry.subject
    d['event_description'] = entry.event_description
    d['email_subject'] = entry.email_subject
    d['email_message'] = entry.email_message
    d['icon'] = entry.icon
    d['color'] = entry.color
    d['event_type'] = entry.event_type
    records.append(d)

print json.dumps({'RECORDS':records}, indent=0, separators=(',',':'))        
