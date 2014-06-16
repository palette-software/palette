import os
import time
import subprocess
import sys

from apscheduler.scheduler import Scheduler
from apscheduler.jobstores.sqlalchemy_store import SQLAlchemyJobStore
from apscheduler.job import Job
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from akiri.framework.ext.sqlalchemy import meta

from event_control import EventControl

global server

class Sched(object):

    JOBSTORE='sjs'

    def __init__(self, in_server):
        global server
        server = in_server

        self.telnet_hostname = server.config.get("palette", "telnet_hostname",
                                                      default="localhost")

        self.telnet_port = server.config.getint("palette", "telnet_port",
                                                            default=9000)

        self.sched_dir = server.config.get("palette", "sched_dir",
                                                default="/var/palette/sched")

        self.command_info = {'telnet_hostname': self.telnet_hostname,
                        'telnet_port': str(self.telnet_port),
                        'envid': str(server.environment.envid),
                        'sched_dir': self.sched_dir}

        sqlalchemy_job_store = SQLAlchemyJobStore(engine=meta.engine)

        self.sched = Scheduler(standalone=False, daemonic=True)
        self.sched.add_jobstore(sqlalchemy_job_store, self.JOBSTORE)

        self.sched.start()
        self.sched.add_listener(Sched.listener,
                                        EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    def status(self):
        jobs = self.sched.get_jobs()
        jlist = []
        for job in jobs:
            jlist.append(self.job_to_dict(job))

        return {'jobs': jlist}

    def delete(self, names):
        deleted = []
        failed = []
        not_found = []
        for jobname in names:
            jobs = self.sched.get_jobs()
            found = False
            for job in jobs:
                if jobname == job.name:
                    found = True
                    try:
                        self.sched.unschedule_job(job)
                        deleted.append(self.job_to_dict(job))
                    except KeyError, e:
                        server.log.error("sched delete failed: " + str(e))
                        failed.append(self.job_to_dict(job))
            if not found:
                server.log.info("No such job name: %s", jobname)
                not_found.append(jobname)

        body =  {'deleted': deleted}
        if len(failed):
            body['error'] = "sched del failed"
            body['failed'] = failed
        if len(not_found):
            body['error'] = "sched del failed"
            body['not-found'] = not_found
        return body

    def job_to_dict(self, job):
        return {'name': job.name, 'runs': job.runs, 'trigger': job.trigger}

    def add(self, minute, hour, dom, month, dow, command):
        path = os.path.join(self.command_info['sched_dir'], command)
        if not os.path.exists(path):
            return { 'error': "No such sched command script: " + command}

        try:
            job = self.sched.add_cron_job(\
                Sched.job_function, name=command,
                    args=[command, self.command_info],
                    jobstore=self.JOBSTORE,
                    minute=minute, hour=hour, day=dom, month=month,
                                                                day_of_week=dow)
        except:
            e = sys.exc_info()[0]
            return {'error': e}

        return self.job_to_dict(job)

    def populate(self):
        jobs = self.sched.get_jobs()

        if len(self.sched.get_jobs()):
            server.log.debug("sched populate: already jobs")
            # return - commented out.  For now, always set default jobs.

        # For now, remove all jobs and add them back.
        for job in jobs:
            server.log.debug("sched populate: unscheduling %s", job.name)
            self.sched.unschedule_job(job)

        server.log.debug("sched populate: adding jobs")

        # Backup every night at 12:00.
        self.sched.add_cron_job(Sched.job_function, jobstore=self.JOBSTORE,
            name='backup',
            args=['backup', self.command_info],
            hour=0, minute=0)

        self.sched.add_cron_job(Sched.job_function, jobstore=self.JOBSTORE,
            name='yml',
            args=['yml', self.command_info],
            minute="*/5")

        self.sched.add_cron_job(Sched.job_function, jobstore=self.JOBSTORE,
            name='info_all',
            args=['info_all', self.command_info],
            minute="1,6,11,16,21,26,31,36,41,46,51,56")

        """
        print self.sched.add_cron_job(\
            Sched.job_function, name='license_check',
                args=['license_check', self.command_info],
                max_runs=5,
                                    second="*/5", jobstore=self.JOBSTORE)
        """

    @classmethod
    def listener(cls, event):
        if event.exception:
            server.log.error("listener: Scheduled job failed: %s",
                                                                event.job.name)
        else:
            server.log.debug("listener: Scheduled job started successfully: %s",
                                                                event.job.name)

    @classmethod
    def job_function(cls, command, command_info):
        server.log.debug("sched command: %s, command_info: %s", command,
                                                            str(command_info))
        path = os.path.join(command_info['sched_dir'], command)

        if not os.path.exists(path):
            server.log.error("sched job_function: No such command: %s", path)
            return

        cmd = [ path,
                '--hostname', command_info['telnet_hostname'],
                '--port', command_info['telnet_port'],
                '--envid', command_info['envid']
               ]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, close_fds=True)

        stdout, stderr = process.communicate()

        server.log.debug("cmd '%s' exit status: %d, stdout: '%s', stderr: %s'",
                                path, process.returncode, stdout, stderr)

        if process.returncode:
            server.event_control.gen(EventControl.SCHEDULED_JOB_FAILED,
                {'stdout': stdout,
                    'stderr': stderr,
                    'info': 'Command: ' + command })
        else:
            server.event_control.gen(EventControl.SCHEDULED_JOB_STARTED,
                {'stdout': stdout,
                    'stderr': stderr,
                    'info': 'Command: ' + command })

        return

if __name__ == "__main__":
    command_info = {    'telnet_hostname': "localhost",
                        'telnet_port': 9000,
                        'sched_dir': "/var/palette/sched"}

    Sched.job_function("backup", command_info)
    time.sleep(30)
