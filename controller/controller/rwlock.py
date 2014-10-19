import threading

class RWLock(object):
    """Reader-writer lock.
       Multiple readers can hold the lock simultaneously.
       One writer can be given exclusive access to the lock, without
       any readers holding the lock.
       Write locks have priority over read locks to prevent write
       starvation."""

    def __init__(self):

        # If positive: Number of readers that acquired a read lock.
        # If -1: A writer has the lock
        # If 0: No readers or writers have acquired the lock
        self.rwlock = 0

        self.writers_waiting = 0
        self.monitor = threading.Lock()
        self.readers_ready = threading.Condition(self.monitor)
        self.writers_ready = threading.Condition(self.monitor)

    def read_acquire(self, blocking=True):
        """Acquire a read lock. Several threads can hold this type
           of lock simultaeously.  Readers cannot acquire the lock
           if a writer has the lock.
           Returns (for "blocking=False"):
                True if acquired the lock
                False if didn't acquire the lock.
            """

        self.monitor.acquire()
        while self.rwlock < 0 or self.writers_waiting:
            if not blocking:
                self.monitor.release()
                return False
            # A writer has the rwlock or a writer is waiting for the rwlock
            self.readers_ready.wait()
        self.rwlock += 1
        self.monitor.release()
        return True

    def write_acquire(self):
        """Only one thread can hold the write lock.  No other threads
           can hold any read locks when a writer holds the lock."""
        self.monitor.acquire()
        while self.rwlock != 0:
            self.writers_waiting += 1
            self.writers_ready.wait()
            self.writers_waiting -= 1
        self.rwlock = -1
        self.monitor.release()

    def read_release(self):
        """Release a read lock."""
        self.monitor.acquire()
        if self.rwlock <= 0:
            raise RuntimeError(
                    "read_release: Attempt to release an unacquired read lock")

        # Release our read lock
        self.rwlock -= 1

        self.finish_release()

    def write_release(self):
        """Release a write lock."""
        self.monitor.acquire()
        if self.rwlock < 0:
            # We held the write lock and will now release it.
            self.rwlock = 0
        else:
            raise RuntimeError("write_release: Attempted to release a " + \
                               "write lock, but the write lock isn't held.")
        self.finish_release()

    def finish_release(self):
        """We are called by read_release and write_release to notify
           any appropriate waiting writers (first priority) or readers
           (lower priority).  We must be called with the monitor locked
           acquired which is released here."""

        wake_writers = self.writers_waiting and self.rwlock == 0
        wake_readers = self.writers_waiting == 0
        self.monitor.release()
        if wake_writers:
            self.writers_ready.acquire()
            self.writers_ready.notify()
            self.writers_ready.release()
        elif wake_readers:
            self.readers_ready.acquire()
            self.readers_ready.notifyAll()
            self.readers_ready.release()
