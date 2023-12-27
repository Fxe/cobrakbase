import math
import copy
import logging
from cobrakbase.core.kbasegenome.genome import KBaseGenome
from cobrakbase.core.kbasefba.fbamodel_protein import ModelReactionProtein
from cobra.core import Reaction
from modelseedpy.core.msmodel import get_direction_from_constraints

logger = logging.getLogger(__name__)


def get_for_rev_flux_from_bounds(lb, ub):
    rev_flux = 0
    for_flux = 0
    if lb > ub:
        return 0, 0
    if lb < 0:
        rev_flux = math.fabs(lb)
    if ub > 0:
        for_flux = ub
    return rev_flux, for_flux


def _get_gpr(data):
    gpr = []
    for mrp in data["modelReactionProteins"]:
        # print(mrp.keys())
        gpr_and = []
        for mrps in mrp["modelReactionProteinSubunits"]:
            gpr_or = []
            # print(mrps.keys())
            for feature_ref in mrps["feature_refs"]:
                gpr_or.append(feature_ref.split("/")[-1])
            if len(gpr_or) > 0:
                gpr_and.append(gpr_or)
        if len(gpr_and) > 0:
            gpr.append(gpr_and)
    return gpr


def _get_gpr_string(gpr):
    ors = []
    for ands in gpr:
        a = []
        for orss in ands:
            if len(orss) == 1:
                a.append(orss[0])
            else:
                a.append("(" + " or ".join(orss) + ")")
        if len(a) == 1:
            ors.append(a[0])
        else:
            ors.append("(" + " and ".join(a) + ")")
    if len(ors) == 0:
        return ""
    elif len(ors) == 1:
        return ors[0]
    else:
        return "(" + " or ".join(ors) + ")"


def _get_reaction_constraints_from_direction(data):
    if "direction" in data:
        if data["direction"] == ">":
            return 0, 1000
        elif data["direction"] == "<":
            return -1000, 0
        else:
            return -1000, 1000
    return None, None


def _get_reaction_constraints(data):
    # clean this function !
    if "maxrevflux" in data and "maxforflux" in data:
        if (
            data["maxrevflux"] == 1000000
            and data["maxforflux"] == 1000000
            and "direction" in data
        ):
            return _get_reaction_constraints_from_direction(data)

        return -1 * data["maxrevflux"], data["maxforflux"]
    elif "direction" in data:
        return _get_reaction_constraints_from_direction(data)
    else:
        logger.warning("unable to determine reversibility constraint assume reversible")
        return -1000, 1000


def _build_rxn_id(s):
    if s.startswith("R_"):
        s = s[2:]
    elif s.startswith("R-"):
        s = s[2:]
    str_fix = s
    if "-" in str_fix:
        str_fix = str_fix.replace("-", "__DASH__")
    if not s == str_fix:
        logger.debug("[Reaction] rename: [%s] -> [%s]", s, str_fix)
    return str_fix


COBRA_DATA = [
    "id",
    "name",
    "direction",
    "maxrevflux",
    "maxforflux",
    "modelReactionReagents",
    "protons",
    "probability",
    "pathway",
    "imported_gpr",
]


class ModelReaction(Reaction):
    """
        typedef structure {
            modelreaction_id id; cobra.id
            string name; @optional cobra.name
            string pathway; @optional cobra.subsystem

            reaction_ref reaction_ref;

            Merged together to lower and upper bound
            string direction;
            float maxforflux; @optional
            float maxrevflux; @optional

            float protons;
            float probability;

            modelcompartment_ref modelcompartment_ref; auto generated from compounds

            list<ModelReactionReagent> modelReactionReagents;
            list<ModelReactionProtein> modelReactionProteins;

            mapping<string, list<string>> dblinks; @optional
            list<string> aliases; @optional

            string reference; @optional
            string imported_gpr; @optional
            mapping<string, string> string_attributes; @optional
            mapping<string, float> numerical_attributes; @optional
            mapping<string, mapping<int, tuple<string, bool, list<ModelReactionProtein>>>> gapfill_data; @optional
    } ModelReaction;
    """

    def __init__(
        self,
        reaction_id=None,
        name="",
        subsystem="",
        lower_bound=0.0,
        upper_bound=None,
        protons=None,
        probability=None,
        imported_gpr=None,
        string_attributes=None,
        numerical_attributes=None,
    ):
        super().__init__(reaction_id, name, subsystem, lower_bound, upper_bound)
        self.protons = protons
        self.probability = probability
        self.imported_gpr = imported_gpr
        self.string_attributes = string_attributes
        self.numerical_attributes = numerical_attributes
        self.model_reaction_proteins = None

    SBML_FIELD_PROBABILITY = "ms_probability"

    def _get_probability(self):
        if self.SBML_FIELD_PROBABILITY in self.notes:
            return float(self.notes[self.SBML_FIELD_PROBABILITY])
        else:
            return None

    def _set_probability(self, value: float):
        if not value is None:
            self.notes[self.SBML_FIELD_PROBABILITY] = value

    probability = property(_get_probability, _set_probability)

    @staticmethod
    def from_json(data):
        data_copy = copy.deepcopy(data)
        lower_bound, upper_bound = _get_reaction_constraints(data)
        rxn_id = _build_rxn_id(data["id"])

        reaction = ModelReaction(
            rxn_id,
            data_copy.get("name", ""),
            data_copy.get("pathway", ""),
            lower_bound,
            upper_bound,
            data_copy.get("protons"),
            data_copy.get("probability"),
            data_copy.get("imported_gpr"),
            data_copy.get("string_attributes"),
            data_copy.get("numerical_attributes"),
        )
        reaction.gene_reaction_rule = _get_gpr_string(_get_gpr(data))
        reaction.model_reaction_proteins = [
            ModelReactionProtein.from_json(o) for o in data["modelReactionProteins"]
        ]
        complex_ids = set()
        for complex_data in data.get("modelReactionProteins", []):
            complex_id = complex_data["complex_ref"].split("/")[-1]
            complex_ids.add(complex_id)
        if len(complex_ids) > 0:
            reaction.notes["modelseed_complex"] = ";".join(sorted(list(complex_ids)))

        logger.debug(rxn_id + ":" + _get_gpr_string(_get_gpr(data)))

        for key in data_copy:
            if key not in COBRA_DATA:
                reaction.__dict__[key] = data_copy[key]

        return reaction

    @staticmethod
    def from_cobra_reaction(reaction: Reaction):
        model_reaction = ModelReaction(
            reaction.id,
            reaction.name,
            reaction.subsystem,
            reaction.lower_bound,
            reaction.upper_bound,
        )
        model_reaction.notes = reaction.notes
        model_reaction.annotation = reaction.annotation
        return model_reaction

    @property
    def compartment(self):
        """
        single compartment return its element
        two compartments if e and c return c else return other than c
        (example e/c returns c, m/c returns m, p/c return c)
        """
        # FIXME: fix this, temporary hack this will break if not 0 index
        compartments = self.compartments
        if len(compartments) == 1:
            return list(compartments)[0]

        if "e0" in compartments and "c0" in compartments:
            return "c0"
        elif len(compartments) == 2 and "c0" in compartments:
            return list(compartments - {"c0"})[0]

        return "c0"

    def _get_rev_and_max_min_flux(self):
        rev = get_direction_from_constraints(self.lower_bound, self.upper_bound)
        min_flux, max_flux = get_for_rev_flux_from_bounds(
            self.lower_bound, self.upper_bound
        )
        return rev, max_flux, min_flux

    def _to_json(self):
        rev, max_flux, min_flux = self._get_rev_and_max_min_flux()
        model_reaction_reagents = []
        s = self.metabolites
        for m in s:
            model_reaction_reagents.append(
                {
                    "modelcompound_ref": "~/modelcompounds/id/" + m.id,
                    "coefficient": s[m],
                }
            )

        # FIXME: OLD STUFF NEEDS REVISION
        """
        model_reaction_proteins = []
        if "model_reaction_proteins" in dir(self) and self.model_reaction_proteins:
            model_reaction_proteins = [
                o.get_data() for o in self.model_reaction_proteins
            ]
        """

        proteins_list = []
        if "modelseed_complex" in self.notes:
            for complex_id in self.notes["modelseed_complex"].split(";"):
                if complex_id in self.model.groups:
                    complex_group = self.model.groups.get_by_id(complex_id)
                    model_reaction_protein = {
                        "complex_ref": f"~/template/complexes/name/{complex_id}",
                        "note": complex_group.notes.get("complex_note", ""),
                        "source": complex_group.notes.get("complex_source", ""),
                        "modelReactionProteinSubunits": [],
                    }
                    subunits = {
                        x.split("complex_subunit_features_")[1]
                        for x in complex_group.notes.keys()
                        if x.startswith("complex_subunit_features_")
                    }
                    for su in subunits:
                        su_data = {
                            "role": su,
                            "note": complex_group.notes.get(
                                f"complex_subunit_note_{su}", ""
                            ),
                            "triggering": int(
                                complex_group.notes.get(
                                    f"complex_subunit_triggering_{su}", 1
                                )
                            ),
                            "optionalSubunit": int(
                                complex_group.notes.get(
                                    f"complex_subunit_optional_{su}", 0
                                )
                            ),
                            "feature_refs": [
                                "~/genome/features/id/" + x
                                for x in complex_group.notes[
                                    f"complex_subunit_features_{su}"
                                ].split(";")
                            ],
                        }
                        model_reaction_protein["modelReactionProteinSubunits"].append(
                            su_data
                        )
                    proteins_list.append(model_reaction_protein)
                else:
                    logger.warning(
                        f"IGNORE: reaction {self.id} complex {complex_id} not defined in model.groups"
                    )

        elif "genome" in dir(self.model) and type(self.model.genome) == KBaseGenome:
            from modelseedpy.core.msmodel import get_set_set

            gpr_sets = get_set_set(self.gene_reaction_rule)
            for gpr_cpx in gpr_sets:
                data_cpx = {
                    "complex_ref": "",
                    "modelReactionProteinSubunits": [],
                    "note": "",
                    "source": "",
                }
                for gpr_cpx_subunit in gpr_cpx:
                    # TODO check if gpr_cpx_subunit in self.model.genome
                    data_su = {
                        "feature_refs": ["~/genome/features/id/" + gpr_cpx_subunit],
                        "note": "",
                        "optionalSubunit": 0,
                        "role": "",
                        "triggering": 1,
                    }
                    data_cpx["modelReactionProteinSubunits"].append(data_su)
                model_reaction_proteins.append(data_cpx)

        data = {
            "id": self.id,
            "name": self.name,
            "direction": rev,
            "maxforflux": max_flux,
            "maxrevflux": min_flux,
            "aliases": [],
            "dblinks": {},
            "edits": {},
            "gapfill_data": {},
            "modelReactionProteins": proteins_list,
            "modelReactionReagents": model_reaction_reagents,
            "modelcompartment_ref": "~/modelcompartments/id/" + self.compartment,
            "probability": self.probability if self.probability else 0,
            "protons": self.protons if self.protons else 0,
            "reaction_ref": "~/template/reactions/id/" + self.id[:-1],
        }
        if self.imported_gpr is not None:
            data["imported_gpr"] = self.imported_gpr
        if self.string_attributes is not None:
            data["string_attributes"] = self.string_attributes
        if self.numerical_attributes is not None:
            data["numerical_attributes"] = self.numerical_attributes
        return data
