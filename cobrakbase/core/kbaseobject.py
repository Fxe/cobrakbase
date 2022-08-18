import logging
import copy
from cobra.core.dictlist import DictList
from cobrakbase.kbase_object_info import KBaseObjectInfo
from cobrakbase.exceptions import ObjectError

logger = logging.getLogger(__name__)

KBASE_ARGS = ["provenance", "path", "creator", "orig_wsid", "created",
              "epoch", "refs", "copied", "copy_source_inaccessible"]


class AttrDict(dict):
    """
    Base object to use for subobjects in KBase objects
    """
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class KBaseObject:
    """
    Base object to use for all KBase objects pulled from workspace
    """
    def __init__(self, data=None, info=None, args=None, kbase_type=None, exclude_dict=None):
        """

        :param data:
        :param info:
        :param args:
        :param kbase_type:
        :param exclude_dict:
        """
        #If an object has a key "data", we need to replace it befor setting attributes to the data
        if "data" in data:
            data["_data"] = data["data"]
            del(data["data"])
        data_keys = {}  # keep track of original data keys for deserialization
        for key in data:
            data_keys[key] = type(data[key])

        # Turning all fields in the dictionary into attributes
        if args is None:
            args = {}
        if data is None:
            data = {}
        self.__dict__ = data
        self.exclude_dict = set()
        if exclude_dict:
            self.exclude_dict |= set(exclude_dict)
        self.data_keys = data_keys

        self.info = info
        if self.info is None:
            self.info = KBaseObjectInfo()
        elif type(self.info) is not KBaseObjectInfo:
            raise ObjectError("Wrong info type: {}, expected: {}".format(type(info), KBaseObjectInfo))
        if kbase_type is not None:
            self.info.type = kbase_type
        if self.info.type is None:
            raise ObjectError("KBase object without type")
        self.data = self._from_json(data)

        for field in KBASE_ARGS:
            if field not in args:
                self.__dict__[field] = None
            else:
                self.__dict__[field] = args[field]

    def get_kbase_args(self):
        args = {}
        for k in KBASE_ARGS:
            if k in self.__dict__:
                args[k] = copy.deepcopy(self.__dict__[k])
        return args

    def _to_json(self):
        data = {}
        for key in self.data_keys:
            if self.data_keys[key] is list:
                data[key] = list(map(lambda x: x.get_data() if 'get_data' in dir(x) else x, self.data[key]))
            else:
                data[key] = self.data[key]
        return data

    def _to_object(self, key, data):
        return AttrDict(data)

    def _from_json(self, data):
        # Should find better solution for this ...
        # Converting every list of hashes containing objects with id fields into DictList
        for field in data.keys():
            if isinstance(data[field], list) and len(data[field]) > 0 and field not in self.exclude_dict:
                logger.debug("object field: %s", field)
                if field == "mediacompounds":
                    for item in data[field]:
                        if "id" not in item:
                            item["id"] = item["compound_ref"].split("/").pop()
                            if item["id"] == "cpd00000":
                                item["id"] = item["name"]

                if isinstance(data[field][0], dict) and "id" in data[field][0]:
                    data[field] = DictList(map(lambda x: self._to_object(field, x), data[field]))

        return data

    def get_data(self):
        return self._to_json()


class KBaseObjectBase:

    def __init__(self, json=None, info=None, api=None):
        if json is not None:
            self.data = json
        else:
            self.data = {}
        self.api = api
        self.object_type = None
        self.object_version = None
        self.ws = None
        self.info = info

    @property
    def id(self):
        if 'id' in self.data:
            return self.data['id']
        logger.warning('missing id')
        return None
    
    @property
    def workspace(self):
        return self.ws
    
    @property
    def name(self):
        if 'name' in self.data:
            return self.data['name']
        return None
    
    @property
    def kbase_type(self):
        if '_type' in self.data:
            return self.data['_type']
        return None
    
    @property
    def kbase_type_version(self):
        if 'name' in self.data:
            return self.data['name']
        return None
    
    @property
    def kbase_full_type(self):
        return self.kbase_type + '-' + self.kbase_type_version
