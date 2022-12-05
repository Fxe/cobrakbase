import pytest
from cobrakbase.core.kbasefba.fbamodel_metabolite import ModelCompound


@pytest.fixture
def kbase_metabolite1():
    return {
        "aliases": [],
        "charge": -1,
        "compound_ref": "~/template/compounds/id/cpd00443",
        "dblinks": {},
        "formula": "C7H6NO2",
        "id": "cpd00443_c0",
        "inchikey": "ALYNCZNDIQEVRV-UHFFFAOYSA-M",
        "modelcompartment_ref": "~/modelcompartments/id/c0",
        "name": "ABEE_c0",
        "numerical_attributes": {},
        "smiles": "Nc1ccc(C(=O)[O-])cc1",
        "string_attributes": {},
    }


@pytest.fixture
def kbase_metabolite_minimal():
    return {
        "id": "cpd00443_c0",
        "name": "ABEE_c0",
        "charge": -1,
        "formula": "C7H6NO2",
        "compound_ref": "~/template/compounds/id/cpd00443",
        "modelcompartment_ref": "~/modelcompartments/id/c0",
    }


def test_metabolite_minimal(kbase_metabolite_minimal):
    cpd = ModelCompound.from_json(kbase_metabolite_minimal)
    assert cpd
    assert cpd.name == "ABEE_c0"
    assert cpd.id == "cpd00443_c0"
    assert cpd.compartment == "c0"


def test_metabolite1(kbase_metabolite1):
    cpd = ModelCompound.from_json(kbase_metabolite1)
    assert cpd
    assert cpd.name == "ABEE_c0"
    assert cpd.id == "cpd00443_c0"
    assert cpd.compartment == "c0"


def test_metabolite_minimal_io(kbase_metabolite_minimal):
    cpd = ModelCompound.from_json(kbase_metabolite_minimal)
    assert kbase_metabolite_minimal == cpd._to_json()
