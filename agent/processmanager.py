import os
import shutil
import subprocess
import copy

class ProcessManager(object):

    def __init__(self, xid_dir, pathenv=None):
        self.xid_dir = xid_dir
        if pathenv:
            val = os.environ['PATH']
            if val:
                val = pathenv + os.pathsep + val
            else:
                val = pathenv
            os.environ['PATH'] = val

    def start(self, xid, cmd, env={}, immediate=False):
        dirpath = os.path.join(self.xid_dir, str(xid))
        os.mkdir(dirpath)

        # append/replace values in env to the process environment.
        env = dict(os.environ.items() + env.items())

        if isinstance(cmd, basestring):
            cmd = 'prun '+cmd
        else:
            cmd = ['prun'] + cmd

        # use shell=True since helpers are generally python scripts
        p = subprocess.Popen(cmd, cwd=dirpath, env=env, shell=True)

        self.writefile(xid, 'pid', p.pid)
        self.writefile(xid, 'cmd', cmd)

        if immediate:
            p.wait()
        
    def cleanup(self, xid):
        dirpath = os.path.join(self.xid_dir, str(xid))
        shutil.rmtree(dirpath)

    def getinfo(self, xid):
        dirpath = os.path.join(self.xid_dir, str(xid))
        d = {'xid': xid }
        try:
            d['pid'] = int(self.readfile(xid, 'pid'))
        except:
            pass
        
        if self.isdone(xid):
            d['run-status'] = 'finished';
            try:
                d['exit-status'] = int(self.readfile(xid, 'returncode'))
            except:
                d['exit-status'] = -1
            d['stdout'] = self.readfile(xid, 'stdout')
            d['stderr'] = self.readfile(xid, 'stderr');
        else:
            d['run-status'] = 'running';
        return d;

    def isdone(self, xid):
        dirpath = os.path.join(self.xid_dir, str(xid))
        if not os.path.isdir(dirpath):
            return True
        path = os.path.join(dirpath, 'returncode')
        return os.path.exists(path)

    def writefile(self, xid, name, value):
        path = os.path.join(self.xid_dir, str(xid), name)
        with open(path, 'w') as f:
            f.write(str(value)+'\n')

    def readfile(self, xid, name):
        path = os.path.join(self.xid_dir, str(xid), name)
        with open(path, 'r') as f:
            val = f.read()
        return val.strip()
