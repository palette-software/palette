import time
import sys
import os
import socket

from akiri.framework.api import RESTApplication, DialogPage
from akiri.framework.config import store

from webob import exc

from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
import meta

from akiri.framework.api import RESTApplication

from . import Session
# FIXME: Need Matt's database engine fix (ticket #101).
from . import db_engine

from inits import *
from controller.backup import BackupEntry
from controller.agentstatus import AgentStatusEntry
from controller.domain import Domain, DomainEntry

__all__ = ["BackupApplication"]

class BackupApplication(RESTApplication):

    NAME = 'backup'

    scheduled = 'Thursday, November 7 at 12:00 AM'

    def __init__(self, global_conf):
        super(BackupApplication, self).__init__(global_conf)

        self.domainname = store.get('palette', 'domainname')
        # FIXME: Need Matt's database engine fix (ticket #101).
        self.domain = Domain(db_engine)
        self.domainid = self.domain.id_by_name(self.domainname)

    def send_cmd(self, cmd):
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect(("", CONTROLLER_TELNET_PORT))
        conn.send(cmd + '\n')
        print "sent", cmd
        data = conn.recv(3).strip()
        print "got", data
        if data != 'OK':
            # fix me: do something
            print "Bad result back from the controller."
        conn.close()

    def handle_backup(self):
        self.send_cmd("backup")
        now = time.strftime('%A, %B %d at %I:%M %p')
        return {'last': now,
                'next': self.scheduled }

    def handle_restore(self):
        last_entry = self.get_last_backup()
        if not last_entry:
            print >> sys.syserr, "No backups to restore from!"
            return {'last': "none",
                    'next': self.scheduled }

        hostname = self.get_hostname_by_uuid(last_entry.uuid)

        if hostname:
            self.send_cmd("restore %s:%s" % (hostname, last_entry.name))
        else:
            print "Error: No agent exists with uuid:", last_entry.uuid

    def get_hostname_by_uuid(self, uuid):
        db_session = Session()
        try:
            agent_entry = db_session.query(AgentStatusEntry).\
                join(DomainEntry).\
                filter(DomainEntry.domainid == self.domainid).\
                filter(AgentStatusEntry.uuid == uuid).\
                one()

        except NoResultFound, e:
            return None
        finally:
            db_session.close()

        return agent_entry.hostname

    def get_last_backup(self):
        db_session = Session()
        last_db = db_session.query(BackupEntry).\
            join(AgentStatusEntry).\
            join(DomainEntry).\
            filter(DomainEntry.domainid == self.domainid).\
            order_by(BackupEntry.creation_time.desc()).\
            first()
        db_session.close()
        return last_db

    def handle(self, req):
        if req.method == 'GET':
            last_entry = self.get_last_backup()
            if not last_entry:
                last = "No backups done."
            else:
                last = str(last_entry.creation_time)

            return {'last': last,
                    'next': self.scheduled}
        elif req.method == 'POST':
            if 'action' not in req.POST:
                raise exc.HTTPBadRequest()
            action = req.POST['action'].lower()
            if action == 'backup':
                return self.handle_backup()
            elif action == 'restore':
                return self.handle_restore()
            raise exc.HTTPBadRequest()
        raise exc.HTTPMethodNotAllowed()

class BackupDialog(DialogPage):

    NAME = "backup"
    TEMPLATE = "backup.mako"

    def __init__(self, global_conf):
        super(BackupDialog, self).__init__(global_conf)

        self.domainname = store.get('palette', 'domainname')
        # FIXME: Need Matt's database engine fix (ticket #101).
        self.domain = Domain(db_engine)
        self.domainid = self.domain.id_by_name(self.domainname)

        session = Session()

        # FIXME: use a mapping here.
        query = session.query(BackupEntry, AgentStatusEntry).\
            join(AgentStatusEntry).\
            join(DomainEntry).\
            filter(DomainEntry.domainid == self.domainid)

        self.backup_entries = []
        for backup, agent in query.all():
            data = {}
            data['name'] = backup.name
            data['ip-address'] = agent.ip_address
            data['creation-time'] = str(backup.creation_time)[:19] # Cut off fraction
            self.backup_entries.append(data)
        session.close()
