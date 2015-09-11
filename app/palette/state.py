"""Basic system state reporting."""
# pylint: enable=missing-docstring,relative-import

from akiri.framework import GenericWSGIApplication

from .monitor import known_agents, calculate_main_state

class StateApp(GenericWSGIApplication):
    """Reports the overall system state for the API"""

    def service_GET(self, req):
        """ Handle a GET request """
        agents = known_agents(req.envid)
        main_state = calculate_main_state(req, agents)
        return {'status': 'OK',
                'state': main_state}
