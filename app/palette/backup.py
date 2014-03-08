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

from akiri.framework.api import RESTApplication
from akiri.framework.config import store

from controller import meta

from controller.backup import BackupEntry
from controller.agentstatus import AgentStatusEntry
from controller.domain import Domain

__all__ = ["BackupApplication"]

class BackupApplication(RESTApplication):

    NAME = 'backup'

    scheduled = 'Thursday, November 7 at 12:00 AM'

    def __init__(self, global_conf):
        super(BackupApplication, self).__init__(global_conf)
        self.Session = sessionmaker(bind=meta.engine)

        domainname = store.get('palette', 'domainname')
        self.domain = Domain.get_by_name(domainname, self.Session)
        self.telnet_port = store.getint("palette", "telnet_port", default=9000)

    def send_cmd(self, cmd):
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect(("", self.telnet_port))
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

        displayname = self.get_displayname_by_agentid(last_entry.agentid)

        if displayname:
            self.send_cmd("restore %s:%s" % (displayname, last_entry.name))
        else:
            print "Error: No displayname for agentid=%d uuid=%s" % \
              (last_entry.agentid, last_entry.uuid)

    def get_displayname_by_agentid(self, agentid):
        session = self.Session()
        try:
            agent_entry = session.query(AgentStatusEntry).\
                filter(AgentStatusEntry.agentid == agentid).\
                one()
        except NoResultFound, e:
            return None
        finally:
            session.close()

        return agent_entry.displayname

    def get_last_backup(self):
        session = self.Session()
        last_db = session.query(BackupEntry).\
            join(AgentStatusEntry).\
            filter(AgentStatusEntry.domainid == self.domain.domainid).\
            order_by(BackupEntry.creation_time.desc()).\
            first()
        session.close()
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
        self.Session = sessionmaker(bind=meta.engine)

        domainname = store.get('palette', 'domainname')
        self.domain = Domain.get_by_name(domainname, self.Session)

        session = self.Session()

        # FIXME: use a mapping here.
        query = session.query(BackupEntry, AgentStatusEntry).\
            join(AgentStatusEntry).\
            filter(AgentStatusEntry.domainid == self.domain.domainid)

        self.backup_entries = []
        for backup, agent in query.all():
            data = {}
            data['name'] = backup.name
            data['displayname'] = agent.displayname
            data['creation-time'] = str(backup.creation_time)[:19] # Cut off fraction
            self.backup_entries.append(data)
        session.close()
