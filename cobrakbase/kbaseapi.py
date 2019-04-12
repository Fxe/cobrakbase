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

class KBaseAPI(object):

    def __init__(self, token, dev=False, config=None):
        if config == None:
            self.ws_client = _get_ws_client(token, dev)
        else:
            self.ws_client = WorkspaceClient(config['workspace-url'], token=token)
        
    def get_object(self, id, ws):
        return _get_object_wsc(self.ws_client, id, ws)
    
    def save_object(self, id, ws, otype, data):
        params = {
            'workspace' : ws,
            'objects' : [{
                'data' : data,
                'name' : id,
                'type' : otype
            }]
        }
        return self.ws_client.save_objects(params)
    
    def save_model(self, id, ws, otype, data):
        return self.save_object(id, ws, 'KBaseFBA.FBAModel', data)
    
    def list_objects(self, ws):
        return self.ws_client.list_objects(
            {
                'workspaces' : [ws]
            }
        )
    
    def get_object_info_from_ref(self, ref):
        ref_data = self.ws_client.get_object_info3(
            {
                'objects' : [{'ref' : ref}]
            }
        )
        return KBaseReference(ref_data['infos'][0])
