import copy
from cobrakbase.core.kbaseobject import AttrDict
from cobrakbase.modelseed.modelseed_reaction import to_str2


class NewModelTemplateReaction(AttrDict):

    def __init__(self, data, template=None):
        super().__init__(data)
        self.data = data
        self.template = template

    @property
    def cstoichiometry(self):
        res = {}
        for o in self.templateReactionReagents:
            cpd_id = o['templatecompcompound_ref'].split('/')[-1]
            cmp = '?'
            if self.template:
                if cpd_id in self.template.compcompounds:
                    compcompound = self.template.compcompounds.get_by_id(cpd_id)
                    cmp = compcompound['templatecompartment_ref'].split('/')[-1]
            res[(cpd_id, cmp)] = o['coefficient']
        return res

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

    def build_reaction_string(self, use_metabolite_names=False, use_compartment_names=None):
        cpd_name_replace = {}
        if use_metabolite_names:
            if self.template:
                for cpd_id in set(map(lambda x: x[0], self.cstoichiometry)):
                    name = cpd_id
                    if cpd_id in self.template.compcompounds:
                        ccpd = self.template.compcompounds.get_by_id(cpd_id)
                        cpd = self.template.compounds.get_by_id(ccpd['templatecompound_ref'].split('/')[-1])
                        name = cpd.name
                    cpd_name_replace[cpd_id] = name
            else:
                return self.data['definition']
        return to_str2(self, use_compartment_names, cpd_name_replace)

    def __str__(self):
        return "{id}: {stoichiometry}".format(
            id=self.id, stoichiometry=self.build_reaction_string())
