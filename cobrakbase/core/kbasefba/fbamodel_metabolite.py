import copy
from cobra.core import Metabolite

# data taken to the cobra object
COBRA_DATA = ['id', 'formula', 'name', 'charge', 'modelcompartment_ref']


def build_cpd_id(s):
    if s.startswith("M_"):
        return s[2:]
    if s.startswith("M-"):
        return s[2:]
    return s


class ModelCompound(Metabolite):

    def __init__(self, data, metabolite_id=None, formula=None, name=None, charge=None, compartment=None):
        """
        KBase FBAModel Metabolite is a subclass of cobra.core.Metabolite
        """
        data_copy = copy.deepcopy(data)
        cpd_id = build_cpd_id(data['id'])
        compartment = data_copy['modelcompartment_ref'].split('/')[-1]
        super().__init__(cpd_id,
                         data_copy['formula'],
                         data_copy['name'],
                         data_copy['charge'],
                         compartment)

        for key in data_copy:
            if key not in COBRA_DATA:
                self.__dict__[key] = data_copy[key]

    @staticmethod
    def from_json(data):
        data_copy = copy.deepcopy(data)
        cpd_id = build_cpd_id(data['id'])
        compartment = data_copy['modelcompartment_ref'].split('/')[-1]
        return ModelCompound({}, cpd_id, data_copy['formula'], data_copy['name'], data_copy['charge'], compartment)

    @property
    def compound_id(self):
        cpd_id = self.id
        # remove ending compartment if present
        if cpd_id.endswith(self.compartment):
            cpd_id = cpd_id[: -1 * len(self.compartment)]
            # further remove _ because of compartment
            if cpd_id.endswith('_'):
                cpd_id = cpd_id[:-1]

        return cpd_id

    def _to_json(self):
        return {
            'aliases': [],
            'dblinks': {},
            'numerical_attributes': {},
            'string_attributes': {},
            'charge': self.charge,
            'compound_ref': f'~/template/compounds/id/{self.compound_id}',
            'formula': self.formula,
            'id': self.id,
            'modelcompartment_ref': '~/modelcompartments/id/' + self.compartment,
            'name': self.name
        }
