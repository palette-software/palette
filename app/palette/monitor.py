from akiri.framework.api import RESTApplication, DialogPage

__all__ = ["MonitorApplication"]

class MonitorApplication(RESTApplication):

    NAME = 'monitor'

    def handle(self, req):
        return {'status': 'OK'}

class StatusDialog(DialogPage):

    NAME = "status"
    TEMPLATE = "status.mako"
