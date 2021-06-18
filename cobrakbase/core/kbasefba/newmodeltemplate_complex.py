import copy
from cobrakbase.core.kbaseobject import AttrDict


class NewModelTemplateComplex(AttrDict):

    def __init__(self, data, template=None):
        super().__init__(data)
        self.data = data
        self.template = template

    def get_data(self):
        d = {}
        for k in self:
            if k not in ['data', 'template']:
                d[k] = copy.deepcopy(self[k])
        return d
