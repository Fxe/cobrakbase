class KBaseObjectBase:
    
    def __init__(self, json=None):
        if not json == None:
            self.data = json
        else:
            self.data = {}
            
        self.otype = None
        self.otype_version = None
        
    @property
    def id(self):
        if 'id' in self.data:
            return self.data['id']
        logger.warning('missing id')
        return None
    
    @property
    def name(self):
        if 'name' in self.data:
            return self.data['name']
        return None
    
    @property
    def kbase_type(self):
        if 'name' in self.data:
            return self.data['name']
        return None
    
    @property
    def kbase_type_version(self):
        if 'name' in self.data:
            return self.data['name']
        return None
    
    @property
    def kbase_full_type(self):
        return self.kbase_type + '-' + self.kbase_type_version