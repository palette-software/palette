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

    def get_agent(self, agents, id):
        for i in agents:
            if i.agentid == id:
                return i
        return None

    def handle_get(self, req):
        # populate the storage settings
        query = meta.Session.query(SystemEntry).all()
        storage = []
        item = {}
        for entry in query:
            item[entry.key] = entry.value
        storage.append(item)

        # populate the storage volume locations
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
            agent = self.get_agent(all_agents, i.agentid)
            item = "{0} {1} {2} ({3} Unused)".format( agent.displayname, i.name, sizestr(i.size), sizestr(i.available_space))
            locations['options'].append( {'item': item , 'id': item_count} )
            item_count = item_count + 1

        # set the current selection
        storage_type = storage[0]['backup-dest-type']
        if storage_type == "gcs":
            storage_id = 1
        elif storage_type == "s3":
            storage_id = 2
        elif storage_type == "vol":
            storage_id = int(storage[0]['backup-dest-id']) + 2
        locations['id'] = storage_id
        locations['value'] = locations['options'][storage_id]['item']

        storage.append({'volumes':locations})
        return {'storage': storage}

    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('id', 'value')
    def handle_post(self, req):
        k = req.POST['id']
        v = req.POST['value']
        row = SystemEntry.get_by_key(k)
        if row is None:
            # print error
            pass

        row.value = v
        meta.Session.commit()
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
