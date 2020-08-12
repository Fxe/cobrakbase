import sys
from cobrakbase.Workspace.WorkspaceClient import Workspace as WorkspaceClient

KBASE_WS_URL = "https://kbase.us/services/ws/"
DEV_KBASE_WS_URL = "https://appdev.kbase.us/services/ws/"

class KBaseReference():
    
    def __init__(self, tuple):
        self.tuple = tuple
    
    @property
    def uid(self):
        return self.tuple[0]
    
    @property
    def id(self):
        return self.tuple[1]
    
    @property
    def type(self):
        return self.tuple[2]
    
    @property
    def created_at(self):
        return self.tuple[3]
    
    @property
    def version(self):
        return self.tuple[4]
    
    @property
    def user(self):
        return self.tuple[5]
    
    @property
    def workspace_uid(self):
        return self.tuple[6]
    
    @property
    def workspace_id(self):
        return self.tuple[7]
    
    @property
    def reference(self):
        return "{}/{}/{}".format(self.workspace_uid, self.uid, self.version)
        
    def __str__(self):
        return self.reference
    
    

def _get_object_wsc(wclient, oid, ws):
    res = wclient.get_objects2({"objects" : [{"name" : oid, "workspace" : ws}]})
    return res["data"][0]["data"]

def _get_ws_client(token, dev=False):
    url = KBASE_WS_URL
    if dev:
        url = DEV_KBASE_WS_URL
    return WorkspaceClient(url, token=token)


class KBaseAPI:

    def __init__(self, token, dev=False, config=None):
        if config is None:
            self.ws_client = _get_ws_client(token, dev)
        else:
            self.ws_client = WorkspaceClient(config['workspace-url'], token=token)

    def get_object(self, object_id, ws):
        return _get_object_wsc(self.ws_client, object_id, ws)

    def get_object_by_ref(self, object_ref):
        object_info = self.get_object_info_from_ref(object_ref)
        return self.get_object(object_info.id, object_info.workspace_id)
    
    def save_object(self, object_id, ws, object_type, data):
        from cobrakbase import __version__
        ps = [
            {
                'description': 'COBRA KBase API',
                'input_ws_objects': [],
                'method': 'save_object',
                'script_command_line': f"{sys.version}",
                'method_params': [
                    {
                        'object_id': object_id,
                        'ws': ws,
                        'object_type': object_type
                    }
                ],
                'service': 'cobrakbase.KBaseAPI',
                'service_ver': __version__,
                # 'time': '2015-12-15T22:58:55+0000'
            }
        ]
        params = {
            'workspace': ws,
            'objects': [{
                'data': data,
                'name': object_id,
                'type': object_type,
                'provenance': ps
            }]
        }
        return self.ws_client.save_objects(params)
    
    def save_model(self, object_id, ws, data):
        return self.save_object(object_id, ws, 'KBaseFBA.FBAModel', data)
    
    def list_objects(self, ws):
        return self.ws_client.list_objects(
            {
                'workspaces': [ws]
            }
        )
    
    def get_object_info_from_ref(self, ref):
        ref_data = self.ws_client.get_object_info3(
            {
                'objects': [{'ref' : ref}]
            }
        )
        return KBaseReference(ref_data['infos'][0])
