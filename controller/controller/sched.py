import os
import time
import subprocess
import sys
import threading
import re

from datetime import datetime

from sqlalchemy import Column, String, BigInteger, DateTime, LargeBinary
from sqlalchemy.orm.exc import NoResultFound
from akiri.framework.ext.sqlalchemy import meta

from mixin import BaseDictMixin
from event_control import EventControl
from croniter import Croniter

class Sched(threading.Thread):

    def __init__(self, server):
        super(Sched, self).__init__()
        self.daemon = True

        self.server = server
        self.handler = JobHandler(self)
        self.telnet_hostname = self.server.config.get("palette",
                                                      "telnet_hostname",
                                                      default="localhost")

        self.telnet_port = self.server.config.getint("palette",
                                                     "telnet_port",
                                                     default=9000)

        self.sched_dir = server.config.get("palette",
                                           "sched_dir",
                                           default="/var/palette/sched")

        localtime = datetime.now()
        utc = datetime.utcnow()
        self.utc_ahead = (utc.hour - localtime.hour) % 24

        self.start()

    def run(self):
        while True:      
            now = time.time()
            nexttime = 61 +  now - (now % 60) # start of the minute

            for job in Crontab.get_ready_jobs():
                self.server.log.debug("JOB: " + str(job))
                try:
                    self.handler(job.name)
                except Exception, e:
                    self.server.error("Job '%s':" + str(e))
                job.set_next_run_time()

            meta.Session.commit()
            time.sleep(nexttime - now)

    def add_cron_job(self, name,
                     minute="*", hour="*", day_of_month="*", 
                     month="*", day_of_week="*"):

        entry = Crontab.get(name)
        entry.minute = str(minute)
        if type(hour) == int or hour.isdigit():
            # convert hour to UTC
            hour = (int(hour) + self.utc_ahead) % 24

        entry.hour = str(hour)
        entry.day_of_month = str(day_of_month)
        entry.month = str(month)
        entry.day_of_week = str(day_of_week)

        entry.set_next_run_time()
        meta.Session.commit()
        return {}

    def status(self):
        jlist = [job.todict(pretty=True) for job in Crontab.get_jobs()]
        for job in jlist:
            if job['hour'].isdigit():
                job['hour'] = (int(job['hour']) - self.utc_ahead) % 24
        return {'jobs': jlist}

    def delete(self, names):
        body = {}
        try:
            Crontab.delete(names)
            if isinstance(names, basestring):
                names = [names]
            body['deleted'] = names
        except Exception, e:
            body['status'] = 'FAILED'
            body['error'] = str(e)
        return body

    def populate(self):
        jobs = Crontab.get_jobs()
        if jobs:
            self.server.log.debug("sched populate: already jobs")
            return

        self.server.log.debug("sched populate: adding jobs")

        # Backup every night at 12:00.
        self.add_cron_job(name='backup', hour=0, minute=0)

        self.add_cron_job(name='yml', minute="0/5")
        self.add_cron_job(name='info_all', minute="1/5")
        self.add_cron_job(name='auth_import', minute="2/10")
        self.add_cron_job(name='sync', minute="3/5")
        self.add_cron_job(name='http_request', minute='3/5')
        self.add_cron_job(name='extract', minute="3/5")
        self.add_cron_job(name='workbook', minute='3/5')
        self.add_cron_job(name='license_check', minute="4/5")
        self.add_cron_job(name='checkports', minute="*")


class Crontab(meta.Base, BaseDictMixin):
    __tablename__ = "cron"
    slash_re = re.compile(r'^(\d+)/(\d+)$')

    cronid = Column(BigInteger, unique=True, nullable=False, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    next_run_time = Column(DateTime)
    minute = Column(String, nullable=False) # 0-59,*
    hour = Column(String, nullable=False) # 0-23,*
    day_of_month = Column(String, nullable=False) # 1-31,*
    month = Column(String, nullable=False) # 1-12,*
    day_of_week = Column(String, nullable=False) # 0-6,# or names

    # convert X/Y format to comma delimetted list
    def commafy(self, s, maxval=60):
        m = self.slash_re.match(s)
        if not m:
            return s
        x,y = int(m.group(1)), int(m.group(2))

        retval = ''
        while x < maxval:
            if retval:
                retval = retval + ','
            retval = retval + str(x)
            x = x + y
        return retval

    def __str__(self):
        s = ' '.join([self.minute, self.hour,
                      self.day_of_month,self.month, self.day_of_week])
        return '[' + self.name + '] ' + s

    def expr(self):
        return ' '.join([self.commafy(self.minute),
                         self.commafy(self.hour, maxval=24),
                         self.day_of_month, self.month, self.day_of_week])

    def set_next_run_time(self):
        itr = Croniter(self.expr(), start_time = datetime.utcnow())
        t =  itr.get_next()
        self.next_run_time = datetime.fromtimestamp(t)

    @classmethod
    def get(self, name):
        try:
            entry = meta.Session.query(Crontab).\
                filter(Crontab.name == name).one()
        except NoResultFound:
            entry = Crontab(name=name)
            meta.Session.add(entry)
        return entry

    @classmethod
    def get_ready_jobs(cls):
        return meta.Session.query(Crontab).\
                filter(Crontab.next_run_time <= datetime.utcnow()).\
                order_by(Crontab.cronid).all()

    @classmethod
    def get_jobs(cls):
        return meta.Session.query(Crontab).\
                order_by(Crontab.cronid).all()

    @classmethod
    def delete(cls, arg):
        q = meta.Session.query(Crontab)
        if isinstance(arg, basestring):
            q = q.filter(Crontab.name == arg)
        else:
            q = q.filter(Crontab.name.in_(arg))
        q.delete(synchronize_session='fetch')
        meta.Session.commit()


class JobHandler(object):

    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.server = self.scheduler.server

    def __call__(self, name):
        if self.server.upgrading():
            self.server.log.info(
                "sched command will be SKIPPED due to upgrading.  "
                "command: %s", name)
            return

        self.server.log.debug("sched command: %s", name)
        path = os.path.join(self.scheduler.sched_dir, name)

        if not os.path.exists(path):
            self.server.log.error("sched job: No such command: %s", path)
            self.server.event_control.gen(\
                EventControl.SCHEDULED_JOB_FAILED,
                { 'error': "No such command: '%s'" % name})
            return

        cmd = [ path,
                '--hostname', self.scheduler.telnet_hostname,
                '--port', str(self.scheduler.telnet_port),
                '--envid', str(self.server.environment.envid)
               ]

        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, close_fds=True)
        except Exception as e:
            self.server.event_control.gen(\
                EventControl.SCHEDULED_JOB_FAILED,
                { 'error': "Could not start job '%s': %s" % (cmd, e.__doc__) })
            return

        stdout, stderr = process.communicate()

        self.server.log.debug("cmd '%s' exit status: %d, "
                              "stdout: '%s', stderr: %s'",
                              path, process.returncode, stdout, stderr)
        return    
