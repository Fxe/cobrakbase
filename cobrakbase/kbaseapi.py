from cobrakbase.Workspace.WorkspaceClient import Workspace as WorkspaceClient

KBASE_WS_URL = "https://kbase.us/services/ws/"
DEV_KBASE_WS_URL = "https://appdev.kbase.us/services/ws/"

def _get_object_wsc(wclient, oid, ws):
    res = wclient.get_objects2({"objects" : [{"name" : oid, "workspace" : ws}]})
    return res["data"][0]["data"]

def _get_ws_client(token, dev=False):
    url = KBASE_WS_URL
    if dev:
        url = DEV_KBASE_WS_URL
    return WorkspaceClient(url, token=token)

class KBaseAPI(object):

    def __init__(self, token, dev=False):
        self.ws_client = _get_ws_client(token, dev)
        
    def get_object(self, id, ws):
        return _get_object_wsc(self.ws_client, id, ws)
    
    def list_objects(self, ws):
        return self.ws_client.list_objects(
            {
                'workspaces' : [ws]
            }
        )
    
    def get_object_info_from_ref(self, ref):
        return self.ws_client.get_object_info3(
            {
                'objects' : [{'ref' : ref}]
            }
        )
