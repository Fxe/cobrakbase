class KBaseObjectInfo:
    
    def __init__(self, data=None, object_type=None):
        if data is None:
            self._tuple = [None, None, object_type, None, None, None, None, None, None, None]
        else:
            self._tuple = data

        self._type_version = None
        if self.type:
            array = self.type.split("-")  # can it be not len == 2 ?!
            if len(array) == 2:
                self._type_version = array[1]
                self._tuple[2] = array[0]

    @property
    def uid(self):
        return self._tuple[0]
    
    @property
    def id(self):
        return self._tuple[1]
    
    @property
    def type(self):
        return self._tuple[2]

    @property
    def type_version(self):
        return self._type_version

    @type.setter
    def type(self, object_type):
        self._tuple[2] = object_type

    @property
    def created_at(self):
        return self._tuple[3]
    
    @property
    def version(self):
        return self._tuple[4]
    
    @property
    def user(self):
        return self._tuple[5]
    
    @property
    def workspace_uid(self):
        return self._tuple[6]
    
    @property
    def workspace_id(self):
        return self._tuple[7]

    @property
    def checksum(self):
        return self._tuple[8]

    @property
    def size(self):
        return self._tuple[9]

    @property
    def metadata(self):
        return self._tuple[10]
    
    @property
    def reference(self):
        return "{}/{}/{}".format(self.workspace_uid, self.uid, self.version)
        
    def __str__(self):
        return self.reference
