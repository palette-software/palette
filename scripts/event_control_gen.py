from akiri.framework.sqlalchemy import create_engine

import sys
if len(sys.argv) == 1:
    url = 'postgresql://palette:palpass@localhost/paldb'
elif len(sys.argv) == 2:
    url = sys.argv[1]
else:
    print >> sys.stderr, 'usage: event_control_gen.py [url]'
    sys.exit(1)

create_engine(url, echo=False, pool_size=20, max_overflow=30)

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
    d['event_type_label'] = entry.event_type_label
    d['event_label'] = entry.event_label
    d['event_label_desc'] = entry.event_label_desc
    d['admin_visibility'] = entry.admin_visibility
    d['publisher_visibility'] = entry.publisher_visibility
    records.append(d)

print json.dumps({'RECORDS':records}, indent=0, separators=(',',':'))        
