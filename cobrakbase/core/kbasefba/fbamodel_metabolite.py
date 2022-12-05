import copy
from cobra.core import Metabolite

# data taken to the cobra object
COBRA_DATA = [
    "id",
    "formula",
    "name",
    "charge",
    "compound_ref",
    "modelcompartment_ref",
    "smiles",
    "inchikey",
    "maxuptake",
    "string_attributes",
    "numerical_attributes",
    "aliases",
    "dblinks",
]


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

    def __init__(
        self,
        metabolite_id=None,
        formula=None,
        name=None,
        charge=None,
        compartment=None,
        smiles=None,
        inchikey=None,
        max_uptake=None,
        string_attributes=None,
        numerical_attributes=None,
        db_links=None,
        aliases=None,
    ):
        """
        KBase FBAModel Metabolite is a subclass of cobra.core.Metabolite
        """
        super().__init__(metabolite_id, formula, name, charge, compartment)

        self.inchikey = inchikey
        self.smiles = smiles
        self.max_uptake = max_uptake
        self.string_attributes = string_attributes
        self.numerical_attributes = numerical_attributes
        self.db_links = db_links
        self.aliases = aliases

    def _get_smiles(self):
        return self.annotation.get("smiles")

    def _set_smiles(self, value: str):
        if value:
            self.annotation["smiles"] = value
        else:
            if "smiles" in self.annotation:
                del self.annotation["smiles"]

    smiles = property(_get_smiles, _set_smiles)

    def _get_inchikey(self):
        return self.annotation.get("inchikey")

    def _set_inchikey(self, value: str):
        if value:
            self.annotation["inchikey"] = value

    inchikey = property(_get_inchikey, _set_inchikey)

    def _get_max_uptake(self):
        return self.notes.get("kbase_max_uptake")

    def _set_max_uptake(self, value: float):
        if value:
            self.notes["kbase_max_uptake"] = value

    max_uptake = property(_get_max_uptake, _set_max_uptake)

    def _get_string_attributes(self):
        string_attributes = {}
        for k in self.notes:
            if self.notes[k] and type(self.notes[k]) == str:
                string_attributes[k] = self.notes
        return string_attributes

    @staticmethod
    def from_json(data):
        data_copy = copy.deepcopy(data)
        cpd_id = build_cpd_id(data["id"])
        compartment = data_copy["modelcompartment_ref"].split("/")[-1]
        formula = data_copy.get("formula")
        charge = data_copy.get("charge")
        if type(charge) == float or type(charge) == str:
            charge = int(charge)

        # force formula to be None if either null or * string
        if formula == "*" or formula == "null":
            formula = None

        cpd = ModelCompound(
            cpd_id,
            formula,
            data_copy["name"],
            charge,
            compartment,
            data_copy.get("smiles"),
            data_copy.get("inchikey"),
            data_copy.get("maxuptake"),
            data_copy.get("string_attributes"),
            data_copy.get("numerical_attributes"),
            data_copy.get("dblinks"),
            data_copy.get("aliases"),
        )

        for key in data_copy:
            if key not in COBRA_DATA:
                cpd.__dict__[key] = data_copy[key]

        return cpd

    @staticmethod
    def from_cobra_metabolite(metabolite: Metabolite):
        model_compound = ModelCompound(
            metabolite.id,
            metabolite.formula,
            metabolite.name,
            metabolite.charge,
            metabolite.compartment,
        )
        return model_compound

    def to_cobra_metabolite(self):
        metabolite = Metabolite(
            self.id, self.formula, self.name, self.charge, self.compartment
        )
        metabolite.annotation = copy.deepcopy(self.annotation)
        metabolite.notes = copy.deepcopy(self.notes)

        return metabolite

    @property
    def compound_id(self):
        cpd_id = self.id
        # remove ending compartment if present
        if cpd_id.endswith(self.compartment):
            cpd_id = cpd_id[: -1 * len(self.compartment)]
            # further remove _ because of compartment
            if cpd_id.endswith("_"):
                cpd_id = cpd_id[:-1]

        return cpd_id

    def _to_json(self):
        data = {
            "id": self.id,
            "name": self.name,
            "charge": self.charge,
            "formula": self.formula if self.formula else "null",
            "compound_ref": f"~/template/compounds/id/{self.compound_id}",
            "modelcompartment_ref": f"~/modelcompartments/id/{self.compartment}",
        }

        if self.inchikey is not None:
            data["inchikey"] = self.inchikey
        if self.smiles is not None:
            data["smiles"] = self.smiles
        if self.max_uptake is not None:
            data["maxuptake"] = self.max_uptake
        if self.string_attributes is not None:
            data["string_attributes"] = self.string_attributes
        if self.numerical_attributes is not None:
            data["numerical_attributes"] = self.numerical_attributes
        if self.db_links is not None:
            data["dblinks"] = self.db_links
        if self.aliases is not None:
            data["aliases"] = self.aliases
        return data
