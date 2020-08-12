import logging

logger = logging.getLogger(__name__)


class KBaseObjectBase:
    
    def __init__(self, json=None, api=None):
        if json is not None:
            self.data = json
        else:
            self.data = {}
        self.api = api
        self.object_type = None
        self.object_version = None
        self.ws = None
        
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