import threading

class Manager(object):

    def __init__(self, server):
        self.server = server
        self.envid = self.server.environment.envid
        self.log = self.server.log
        self._lock = threading.RLock()

    def lock(self, blocking=True):
        return self._lock.acquire(blocking=blocking)

    def unlock(self):
        self._lock.release()
