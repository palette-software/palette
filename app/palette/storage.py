from webob import exc

from akiri.framework.ext.sqlalchemy import meta
from akiri.framework.config import store

from controller.profile import UserProfile, Role, Publisher, Admin, License
from controller.auth import AuthManager
from controller.util import DATEFMT
from controller.system import SystemEntry
from controller.domain import Domain
from controller.workbooks import WorkbookEntry, WorkbookUpdatesEntry
from controller.agentinfo import AgentVolumesEntry
from controller.agent import Agent
from controller.util import sizestr

from page import PalettePage
from rest import PaletteRESTHandler, required_parameters, required_role

import json

__all__ = ["StorageApplication"]

class StorageApplication(PaletteRESTHandler):
    NAME = 'storage'

    def __init__(self, global_conf):
        super(StorageApplication, self).__init__(global_conf)

    def get_agent_name(self, agents, id):
        for i in agents:
            if i.agentid == id:
                return i.displayname
        return ""

    def handle_get(self, req):
        query = meta.Session.query(SystemEntry).all()

        storage = []
        item = {}
        for entry in query:
            item[entry.key] = entry.value
        storage.append(item)

        locations = {
            'name': 'storage',
            'options' : [
            {'item':'Choose a Storage Location', 'id':0},
            {'item':'Google Cloud Storage', 'id': 1},
            {'item':'Amazon S3 Storage', 'id': 2},
        ]}
        all_agents = meta.Session.query(Agent).all()
        all_volumes = meta.Session.query(AgentVolumesEntry).all()
        item_count = 3
        for i in all_volumes:
            item = "{0} {1} {2} ({3} Unused)".format( self.get_agent_name(all_agents, i.agentid), i.name, sizestr(i.size), sizestr(i.available_space))
            locations['options'].append( {'item': item , 'id': item_count} )
            item_count = item_count + 1

        locations['id'] = 1
        locations['value'] = locations['options'][1]['item']

        storage.append({'volumes':locations})
        return {'storage': storage}

    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('id', 'value')
    def handle_post(self, req):
        key = req.POST['id']
        value = req.POST['value']
        if key == "main_warning":
            pass
        elif key == "main_error":
            pass
        elif key == "other_warning":
            pass
        elif key == "other_error":
            pass        
        return {}

    def handle(self, req):
        if req.method == "GET":
            return self.handle_get(req)
        if req.method == "POST":
            return self.handle_post(req)
        else:
            raise exc.HTTPBadRequest()

class StoragePage(PalettePage):
    TEMPLATE = "storage.mako"
    active = 'storage'
    expanded = True
    required_role = Role.MANAGER_ADMIN

    def handle(self, req):
        return None

def make_storage(global_conf):
    return StoragePage(global_conf)
