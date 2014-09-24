#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Test alert sending emails.
# You will need to set PYTHONPATH for this to work.

from controller.alert_email import AlertEmail
from controller.event_control import EventControl

class EventFake(object):
    def __init__(self):
        #pylint: disable=line-too-long
        self.email_subject = u"ERROR - Tableau Server Partial Process Failure"
        self.email_message = u"""Status: ERROR\n\nPlease review the output below to find which Tableau Process is “Stopped.” Sometimes a Tableau Process will stop running momentarily to restart itself which can cause this alert to be triggered. Normally, Tableau Server will recover in less than 5 minutes. If not, please inspect the Server browser by clicking on the Status box in the top left corner to help you troubleshoot further. \n\nDetails: ${stdout}"""

        self.key = EventControl.STATE_DEGRADED
        self.level = EventControl.LEVEL_ERROR

def test():
    alert_email = AlertEmail(1, standalone=True)
    entry = EventFake()

    data = {'stdout': 'This is the stdout contents'}
    alert_email.send(entry, data)

if __name__ == "__main__":
    # FIXME: make a test email alert in the cli (and remove this)
    test()
