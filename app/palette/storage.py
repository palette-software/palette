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
            {'item':'Google Cloud Storage', 'id': 0},
            {'item':'Amazon S3 Storage', 'id': 1},
        ]}
        all_volumes = meta.Session.query(AgentVolumesEntry).all()
        item_count = len(locations['options'])
        for i in all_volumes:
            agent = Agent.get_by_id(i.agentid)
            item = "{0} {1} {2} ({3} Unused)".format( agent.displayname, i.name, sizestr(i.size), sizestr(i.available_space))
            locations['options'].append( {'item': item , 'id': item_count} )
            item_count = item_count + 1

        # set the current selection
        storage_type = storage[0]['backup-dest-type']
        if storage_type == "gcs":
            storage_id = 0
        elif storage_type == "s3":
            storage_id = 1
        elif storage_type == "vol":
            if storage[0]['backup-dest-id'] is not None:
                storage_id = int(storage[0]['backup-dest-id']) + 1
            else:
                storage_id = 0
        locations['id'] = storage_id
        locations['value'] = locations['options'][storage_id]['item']

        storage.append({'volumes':locations})
        return {'storage': storage}

    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('id', 'value')
    def handle_post(self, req):
        k = req.POST['id']
        v = req.POST['value']
        
        if k == "storage-encrypt":
            if v == '0': 
                v='no' 
            elif v=='1':
                v='yes'

        row = SystemEntry.get_by_key(k)
        # the row key should already be there in the table, but if it is not we create it and set it
        if row is not None:
            row.value = v
        else:
            # TODO fix when we have multiple envs
            row = SystemEntry(envid=1, key=k, value=v)
            meta.Session.add(row)
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

def make_storage(global_conf):
    return StoragePage(global_conf)
