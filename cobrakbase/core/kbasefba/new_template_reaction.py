import copy
from cobrakbase.core.kbaseobject import AttrDict


class NewModelTemplateReaction(AttrDict):

    def __init__(self, data, template=None):
        super().__init__(data)
        self.data = data
        self.template = template

    def remove_role(self):
        pass

    def get_roles(self):
        res = set()
        for complexes in self.data['templatecomplex_refs']:
            complex_id = complexes.split('/')[-1]
            cpx = self.template.get_complex(complex_id)

            for complexrole in cpx['complexroles']:
                role_id = complexrole['templaterole_ref'].split('/')[-1]
                res.add(role_id)

        return res

    def get_complexes(self):
        res = set()
        for complexes in self.data['templatecomplex_refs']:
            complex_id = complexes.split('/')[-1]
            res.add(complex_id)

        return res

    def get_complex_roles(self):
        res = {}
        for complexes in self.data['templatecomplex_refs']:
            complex_id = complexes.split('/')[-1]
            res[complex_id] = set()
            if self.template:
                cpx = self.template.get_complex(complex_id)

                if cpx:
                    for complex_role in cpx['complexroles']:
                        role_id = complex_role['templaterole_ref'].split('/')[-1]
                        res[complex_id].add(role_id)
                else:
                    print('!!')
        return res

    def get_data(self):
        d = {}
        for k in self:
            if k not in ['data', 'template']:
                d[k] = copy.deepcopy(self[k])
        return d
