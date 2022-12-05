import logging
import os
import json
from cobrakbase.kbaseapi import KBaseAPI
from cobrakbase.core.kbase_object_factory import KBaseObjectFactory

logger = logging.getLogger(__name__)


class KBaseCache(KBaseAPI):
    """
    API version that caches the json output in local filesystem for future access
    """

    def __init__(self, token=None, dev=False, config=None, path=None):
        super().__init__(token, dev, config)
        if path is None:
            path = "~/.kbase/cache/" + ("dev" if dev else "prod")
        if not os.path.exists(path):
            os.makedirs(path)
            logger.warning(f"created folder(s) [{path}]")
        if not os.path.exists(path) or not os.path.isdir(path):
            raise ValueError(f"path [{path}] does not exist or is not directory")
        self.path = path

    def get_from_ws(self, id_or_ref, workspace=None):
        info = self.get_object_info(id_or_ref, workspace)
        file_name = f"{info.id}.v{info.version}.json"
        object_path = f"{self.path}/{info.workspace_uid}"

        # we make the folder for the workspace if it does not exists
        if not os.path.exists(object_path):
            os.makedirs(object_path)
            logger.warning(f"created folder(s) [{object_path}]")

        # if json file does not exists fetch and save it otherwise read it from local
        _data = None
        if not os.path.exists(f"{object_path}/{file_name}"):
            res = self.get_objects2(
                {"objects": [self.process_workspace_identifiers(id_or_ref, workspace)]}
            )
            if res is None:
                return None
            _data = res["data"][0]
            with open(f"{object_path}/{file_name}", "w") as fh:
                fh.write(json.dumps(_data))
            logger.debug(f"created file [{object_path}/{file_name}]")
        else:
            with open(f"{object_path}/{file_name}", "r") as fh:
                _data = json.load(fh)

        if _data is None:
            return None
        factory = KBaseObjectFactory()
        return factory.create({"data": [_data]}, None)
