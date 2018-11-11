from cobrakbase.Workspace.WorkspaceClient import Workspace as WorkspaceClient

KBASE_WS_URL = "https://kbase.us/services/ws/"
DEV_KBASE_WS_URL = "https://appdev.kbase.us/services/ws/"

def get_object_wsc(wclient, oid, ws):
    res = wclient.get_objects2({"objects" : [{"name" : oid, "workspace" : ws}]})
    return res["data"][0]["data"]

def get_ws_client(token, dev=False):
    url = KBASE_WS_URL
    if dev:
        url = DEV_KBASE_WS_URL
    return WorkspaceClient(url, token=token)

class KBaseAPI(object):

    def __init__(self, token, dev=False):
        self.wsClient = get_ws_client(token, dev)
        
    def get_object(self, id, ws):
        return get_object_wsc(self.wsClient, id, ws)

