import sys
import time
import logging
import cobra
import os
import requests
import json
from pathlib import Path
from cobrakbase.Workspace.WorkspaceClient import Workspace as WorkspaceClient
from cobrakbase.AbstractHandleClient import AbstractHandle as HandleService
from cobrakbase.kbase_object_info import KBaseObjectInfo
from cobrakbase.core.kbase_object_factory import KBaseObjectFactory
from cobrakbase.Workspace.baseclient import ServerError
from cobrakbase.core.kbaseobject import KBaseObject
from cobrakbase.exceptions import ShockException

logger = logging.getLogger(__name__)

KBASE_WS_URL = "https://kbase.us/services/ws/"
KBASE_HANDLE_URL = "https://kbase.us/services/handle_service"
KBASE_SHOCK_URL = "https://kbase.us/services/shock-api"
DEV_KBASE_WS_URL = "https://appdev.kbase.us/services/ws/"


# Can we eliminate this now?
def _get_object_wsc(wclient, oid, ws):
    res = wclient.get_objects2({"objects": [{"name": oid, "workspace": ws}]})
    return res["data"][0]["data"]


# Why not put this in the constructor?
def _get_ws_client(token, dev=False):
    url = KBASE_WS_URL
    if dev:
        url = DEV_KBASE_WS_URL
    return WorkspaceClient(url, token=token)


class KBaseAPI:

    def __init__(self, token=None, dev=False, config=None):
        self.max_retry = 3
        self.token = token
        if token is None and Path(str(Path.home()) + '/.kbase/token').exists():
            with open(str(Path.home()) + '/.kbase/token', 'r') as fh:
                token = fh.read().strip()
        if token is None:
            raise Exception("missing token value or ~/.kbase/token file")

        if config is None:
            self.ws_client = _get_ws_client(token, dev)
            self.hs = HandleService(KBASE_HANDLE_URL, token=token)
        else:
            self.ws_client = WorkspaceClient(config['workspace-url'], token=token)

    @staticmethod
    def process_workspace_identifiers(id_or_ref, workspace=None):
        """
        IDs should always be processed through this function so we can interchangeably use
        refs, IDs, and names for workspaces and objects
        """
        objspec = {}
        if workspace is None:
            objspec["ref"] = id_or_ref
        else:
            if isinstance(workspace, int):
                objspec['wsid'] = workspace
            else:
                objspec['workspace'] = workspace
            if isinstance(id_or_ref, int):
                objspec['objid'] = id_or_ref
            else:
                objspec['name'] = id_or_ref
        return objspec

    @staticmethod
    def check_response(r):
        if not r.ok:
            errtxt = ('Error downloading file from shock ' +
                      'node {}: ').format(file_id)
            try:
                err = json.loads(response.content)['error'][0]
            except Exception as e:
                # this means shock is down or not responding.
                logger.error("Couldn't parse response error content from Shock: %s", r.content)
                r.raise_for_status()
            raise ShockException(errtxt + str(err))
        pass

    def download_file_from_kbase(self, token, file_id, file_path, is_handle_ref=1):
        """
        FIXME: THIS SEEMS TO DOWNLOAD THE FILE TWICE !
        :param token:
        :param file_id:
        :param file_path:
        :param is_handle_ref:
        :return:
        """
        headers = {'Authorization': 'OAuth ' + token}

        if is_handle_ref == 1:
            handles = self.hs.hids_to_handles([file_id])
            file_id = handles[0]['id']

        if not os.path.exists(file_path):
            try:
                os.makedirs(file_path)
            except OSError as exc:
                print(exc)
                raise
        elif not os.path.isdir(file_path):
            raise ShockException("file_path: %s must be directory", file_path)

        node_url = KBASE_SHOCK_URL + '/node/' + file_id
        r = requests.get(node_url, headers=headers, allow_redirects=True)

        if not r.ok:
            errtxt = 'Error downloading file from shock node {}: '.format(file_id)
            raise ShockException(errtxt)

        resp_obj = r.json()
        size = resp_obj['data']['file']['size']
        if not size:
            raise ShockException('Node {} has no file'.format(file_id))

        node_file_name = resp_obj['data']['file']['name']
        attributes = resp_obj['data']['attributes']
        if os.path.isdir(file_path):
            file_path = os.path.join(file_path, node_file_name)
        with open(file_path, 'wb') as fh:
            with requests.get(node_url + '?download_raw', stream=True, headers=headers, allow_redirects=True) as r:
                if not r.ok:
                    errtxt = 'Error downloading file from shock node {}: '.format(file_id)
                    raise ShockException(errtxt)
                for chunk in r.iter_content(1024):
                    if not chunk:
                        break
                    fh.write(chunk)
        return file_path

    # TODO - really we should explicitly catch time out errors and retry only after those and fail for all others
    def get_objects2(self, args):
        """
        All functions calling get_objects2 should call this function to ensure they get the retry
        code because workspace periodically times out
        """
        tries = 0
        while tries < self.max_retry:
            try:
                return self.ws_client.get_objects2(args)
            except ServerError as e:
                if e.code == -32400:
                    logger.error(e.message)
                    return None
                if e.code == -32500:
                    logger.warning(e.message)
                    return None
                logger.warning("Workspace get_objects2 call failed [%s:%s - %s]. Trying again!",
                               e.name, e.code, e.message)
                tries += 1
                time.sleep(500)  # Give half second
        logger.warning("get_objects2 failed after multiple tries: %s", sys.exc_info()[0])
        raise

    def get_object(self, object_id, ws):
        res = self.get_objects2({"objects": [self.process_workspace_identifiers(object_id, ws)]})
        if res is None:
            return None
        return res["data"][0]["data"]

    def get_from_ws(self, id_or_ref, workspace=None):
        res = self.get_objects2({"objects": [self.process_workspace_identifiers(id_or_ref, workspace)]})
        if res is None:
            return None
        factory = KBaseObjectFactory()
        return factory.create(res, None)

    def save_object(self, object_id, ws, object_type, data, meta=None):
        if not meta:
            if 'get_metadata' in dir(data):
                meta = data.get_metadata()
            else:
                meta = {}
        to_save = data
        if isinstance(data, KBaseObject):
            to_save = data.get_data()
        elif 'get_data' in dir(data):
            to_save = data.get_data()
        # TODO temporary hack implement proper object serializer mapping later
        if type(data) == cobra.core.model.Model:
            from cobrakbase.core.kbasefba.fbamodel_from_cobra import CobraModelConverter
            json, fbamodel = CobraModelConverter(data, None, None).build()
            json['id'] = object_id # rename object id to the saved object_id
            # TODO use fbamodel in the future after fixing FBAModel serializer
            to_save = json
        from cobrakbase import __version__
        provenance = [
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
            'objects': [{
                'data': to_save,
                'name': object_id,
                'type': object_type,
                'meta': meta,
                'provenance': provenance
            }]
        }
        if isinstance(ws, int):
            params["id"] = ws
        else:
            params["workspace"] = ws
        return self.ws_client.save_objects(params)

    def save_model(self, object_id, ws, data):
        return self.save_object(object_id, ws, 'KBaseFBA.FBAModel', data)

    def list_objects(self, ws):
        return self.ws_client.list_objects(
            {
                'workspaces': [ws]
            }
        )

    def get_object_info(self, id_or_ref, workspace=None):
        ref_data = self.ws_client.get_object_info3(
            {
                'objects': [self.process_workspace_identifiers(id_or_ref, workspace)]
            }
        )
        return KBaseObjectInfo(ref_data['infos'][0])

    # TODO: this now seems obfuscated by get_object_info - can we delete this?
    def get_object_info_from_ref(self, ref):
        """
        @deprecated get_object_info
        """
        return self.get_object_info(ref)

    # TODO: this now seems obfuscated by get_object - can we delete this?
    def get_object_by_ref(self, object_ref):
        """
        @deprecated get_object
        """
        return self.get_object(object_ref)
