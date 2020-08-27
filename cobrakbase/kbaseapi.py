import sys
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

    def get_object(self, object_id, ws):
        return _get_object_wsc(self.ws_client, object_id, ws)

    def get_from_ws(self, id_or_ref, workspace=None):
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

        output = self.ws_client.get_objects2({"objects": [objspec]})
        factory = KBaseObjectFactory()
        return factory.create(output, None)

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
        return KBaseObjectInfo(ref_data['infos'][0])
