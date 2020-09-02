import sys
import time
from pathlib import Path
from cobrakbase.Workspace.WorkspaceClient import Workspace as WorkspaceClient
from cobrakbase.kbase_object_info import KBaseObjectInfo
from cobrakbase.core.kbase_object_factory import KBaseObjectFactory

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


class KBaseAPI:

    def __init__(self, token=None, dev=False, config=None):
        if token is None and Path(str(Path.home()) + '/.kbase/token').exists():
            with open(str(Path.home()) + '/.kbase/token', 'r') as fh:
                token = fh.read().strip()
        if token is None:
            raise Exception("missing token value or ~/.kbase/token file")

        if config is None:
            self.ws_client = _get_ws_client(token, dev)
        else:
            self.ws_client = WorkspaceClient(config['workspace-url'], token=token)

    #IDs should always be processed through this function so we can interchangeably use refs, IDs, and names for workspaces and objects
    def process_workspace_identifiers(self,id_or_ref, workspace=None):
        objspec = {}
        if workspace is None:
            objspec["ref"] = id_or_ref
        else:
            if isinstance(workspace, int):
                objspec['wsid'] = workspace
            else:
                objspec['workspace'] = workspace
            if isinstance(workspace, int):
                objspec['objid'] = id_or_ref
            else:
                objspec['name'] = id_or_ref
        return objspec
    
    #All functions calling get_objects2 should call this function to ensure they get the retry code because workspace periodically times out
    def get_object2(self,args):
        tries = 0
        while tries < 3:
            try:
                return self.ws_client.get_objects2(args)
            except:
                print("Workspace get_objects2 call failed. Trying again!")
                tries += 1
                time.sleep(10)
        raise Exception("get_objects2 failed after multiple tries")
       
    def get_object(self, object_id, ws):
        return self.get_object2(self.process_workspace_identifiers(object_id,ws))["data"][0]["data"]

    def get_from_ws(self, id_or_ref, workspace=None):
        output = self.get_objects2(self.process_workspace_identifiers(id_or_ref,workspace))
        factory = KBaseObjectFactory()
        return factory.create(output, None)

    def get_object_by_ref(self, object_ref):
        return self.get_object(object_ref, None)
    
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
        return KBaseObjectInfo(ref_data['infos'][0])
