import copy
from cobra.core import Metabolite

# data taken to the cobra object
COBRA_DATA = ['id', 'formula', 'name', 'charge', 'modelcompartment_ref', 'smiles', 'inchikey', 'maxuptake',
              'string_attributes', 'numerical_attributes']


def build_cpd_id(s):
    if s.startswith("M_"):
        return s[2:]
    if s.startswith("M-"):
        return s[2:]
    return s


class ModelCompound(Metabolite):
    """
    typedef structure {
        modelcompound_id id;
        compound_ref compound_ref;
        string name;
        float charge;
        string formula;
        modelcompartment_ref modelcompartment_ref;
        mapping<string, list<string>> dblinks; @optional
        mapping<string, string> string_attributes; @optional
        mapping<string, float> numerical_attributes; @optional
        list<string> aliases; @optional
        float maxuptake; @optional
        string smiles; @optional
        string inchikey; @optional
    } ModelCompound;
    """

    def __init__(self, metabolite_id=None, formula=None, name=None, charge=None, compartment=None,
                 smiles=None, inchi_key=None, max_uptake=None,
                 string_attributes=None, numerical_attributes=None, db_links=None):
        """
        KBase FBAModel Metabolite is a subclass of cobra.core.Metabolite
        """
        super().__init__(metabolite_id, formula, name, charge, compartment)
        self.smiles = smiles
        self.max_uptake = max_uptake
        self.inchi_key = inchi_key
        self.string_attributes = string_attributes
        self.numerical_attributes = numerical_attributes
        self.db_links = db_links

    @staticmethod
    def from_json(data):
        data_copy = copy.deepcopy(data)
        cpd_id = build_cpd_id(data['id'])
        compartment = data_copy['modelcompartment_ref'].split('/')[-1]
        formula = data_copy.get('formula')
        charge = data_copy.get('charge')
        if type(charge) == float or type(charge) == str:
            charge = int(charge)
        if formula == '*':
            formula = None

        cpd = ModelCompound(cpd_id, formula, data_copy['name'], charge, compartment,
                            data_copy.get('smiles'), data_copy.get('inchikey'), data_copy.get('maxuptake'),
                            data_copy.get('string_attributes'), data_copy.get('numerical_attributes'),
                            data_copy.get('dblinks'))

        for key in data_copy:
            if key not in COBRA_DATA:
                cpd.__dict__[key] = data_copy[key]

        return cpd

    @staticmethod
    def from_cobra_metabolite(metabolite: Metabolite):
        return ModelCompound(metabolite.id, metabolite.formula, metabolite.name,
                             metabolite.charge, metabolite.compartment)

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
        data = {
            'id': self.id,
            'name': self.name,
            'charge': self.charge,
            'formula': self.formula,
            'compound_ref': f'~/template/compounds/id/{self.compound_id}',
            'modelcompartment_ref': f'~/modelcompartments/id/{self.compartment}',
        }
        if self.smiles is not None:
            data['smiles'] = self.smiles
        if self.inchi_key is not None:
            data['inchikey'] = self.inchi_key
        if self.max_uptake is not None:
            data['maxuptake'] = self.max_uptake
        if self.string_attributes is not None:
            data['string_attributes'] = self.string_attributes
        if self.numerical_attributes is not None:
            data['numerical_attributes'] = self.numerical_attributes
        if self.db_links is not None:
            data['dblinks'] = self.db_links
        return data
