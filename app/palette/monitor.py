from akiri.framework.api import RESTApplication

__all__ = ["MonitorApplication"]

class MonitorApplication(RESTApplication):

    NAME = 'monitor'

    def handle(self, req):
        return {'status': 'OK'}
