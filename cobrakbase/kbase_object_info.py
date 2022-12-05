class KBaseObjectInfo:
    def __init__(self, data=None, object_type=None):
        if data is None:
            self._tuple = [
                None,
                None,
                object_type,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ]
        else:
            self._tuple = data

        self._type_version = None
        if self.type:
            array = self.type.split("-")  # can it be not len == 2 ?!
            if len(array) == 2:
                self._type_version = array[1]
                self._tuple[2] = array[0]

    @staticmethod
    def from_kbase_json(d):
        info = KBaseObjectInfo(d)
        return info

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
        if self.workspace_uid is None or self.uid is None or self.version is None:
            return None
        return "{}/{}/{}".format(self.workspace_uid, self.uid, self.version)

    def to_kbase_json(self):
        return self._tuple

    def __str__(self):
        ref = self.reference
        if ref:
            return ref
        else:
            return "0/0/0"
