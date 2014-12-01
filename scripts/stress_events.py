#!/usr/bin/python

from akiri.framework.ext.sqlalchemy import meta

import sqlalchemy
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.exc import NoResultFound
from mako.template import Template
from mako.exceptions import MakoException

from controller.event_control import EventControl
from controller.event import EventEntry
from controller.util import DATEFMT

from datetime import datetime
from time import sleep
import sys
import argparse
import json

def get_event_control_entry(key):
    try:
       entry = meta.Session.query(EventControl).\
          filter(EventControl.key == key).one()
    except NoResultFound:
          return None
    return entry

# default settings
db_url = 'postgresql://palette:palpass@localhost/paldb'
interval_ms = 1000.0
filename = 'stress_events.json'
num_events = 1000
envid = 1
site_id = 1
userid = 1
eventid = 1

# parse the arguments
parser = argparse.ArgumentParser(description='Events Stress tool that generates events based on an input JSON file')
parser.add_argument('-d', '--db', help='DB URL (eg. {0})'.format(db_url), required=False)
parser.add_argument('-i', '--interval', help='Interval in ms', required=False)
parser.add_argument('-f', '--filename', help='Filename of the JSON event file', required=False)
parser.add_argument('-e', '--eventid', help='Starting Event ID', required=False)
parser.add_argument('-n', '--num_events', help='Number of events', required=False)

args = vars(parser.parse_args())

db_url = args['db'] or db_url
interval_ms = args['interval'] or interval_ms
filename = args['filename'] or filename
eventid = args['eventid'] or eventid
num_events = args['num_events'] or num_events;

print 'Genrating {0} events'.format(num_events)

# connect to the DB
meta.engine = sqlalchemy.create_engine(db_url, echo=False)
meta.Base.metadata.create_all(bind=meta.engine)
meta.Session = scoped_session(sessionmaker(bind=meta.engine))
session = meta.Session()

########
interval_sec = float(interval_ms) / 1000.0
count = 0

# load all the data
with open(filename, "r") as f:
    all_events = json.load(f)

while count < int(num_events):

    for i in all_events['RECORDS']:
        key = i['key']
        data = i['data']

        item = get_event_control_entry(key)

        # patch in values
        data['eventid'] = eventid

        # convert the template with the data
        try:
    	    mako_template = Template(item.event_description, default_filters=['h'])
            event_description = mako_template.render(**data)
        except MakoException:
            event_description = \
	        "Mako template message conversion failure: " + \
                 exceptions.text_error_template().render() + \
                 "\ntemplate: " + item.event_description + \
        	 "\ndata: " + str(events[0])
		
        # create an entry
        entry = EventEntry(complete=True)
        key = item.key 
        level = item.level 
        title = item.subject % data 
        icon = item.icon 
        color = item.color
        event_type = item.event_type
        summary = datetime.now().strftime(DATEFMT)
        timestamp = datetime.now()

        print title
        print event_description

        entry.complete = True
        entry.key = key
        entry.envid = envid
        entry.title = title
        entry.description = event_description
        entry.level = level
        entry.icon = icon
        entry.color = color
        entry.event_type = event_type
        entry.summary = summary
        entry.userid = userid
        entry.site_id = site_id
        entry.timestamp = timestamp

        session.add(entry)
        session.commit()

        eventid = eventid + 1

    count = count + 1
    sleep(interval_sec)

print 'Done Generating Events'
