import time
import datetime
from dateutil import tz as dtz

# pylint: disable=invalid-name
class tzlocal(dtz.tzlocal):
    def utcoffset(self, dt):
        self._std_offset = datetime.timedelta(seconds=-time.timezone)
        if time.daylight:
            self._dst_offset = datetime.timedelta(seconds=-time.altzone)
        else:
            self._dst_offset = self._std_offset
        if self._isdst(dt):
            return self._dst_offset
        else:
            return self._std_offset

tzutc = dtz.tzutc
