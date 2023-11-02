import logging

from cobra.core.dictlist import DictList

from cobrakbase.core.kbaseobject import KBaseObjectBase, KBaseObject
from cobrakbase.core.utils import seed_coefficients_to_string
from cobrakbase.core.utils import get_str, get_int, get_id_from_ref

logger = logging.getLogger(__name__)


class KBaseFBASolution(KBaseObjectBase):
    def get_reaction_variable_by_id(self, rxn_id):
        for v in self.dara["FBAReactionVariables"]:
            v_id = v["modelreaction_ref"].split("/")[-1]
            if rxn_id == v_id:
                return v
        return None

    @property
    def objective_value(self):
        return self.data["objectiveValue"]


class KBaseFBAModelCompartment(KBaseObjectBase):
    pass


class KBaseFBAModelMetabolite(KBaseObjectBase):
    @property
    def formula(self):
        return get_str("formula", None, self.data)

    @property
    def charge(self):
        return get_int("charge", 0, self.data)

    @property
    def compartment(self):
        return self.data["modelcompartment_ref"].split("/")[-1]

    @property
    def annotation(self):
        annotation = {}
        if "dblinks" in self.data:
            for db in self.data["dblinks"]:
                if db == "BiGG2":
                    annotation["bigg.metabolite"] = self.data["dblinks"][db][0]
                if db == "LigandCompound":
                    annotation["kegg.compound"] = self.data["dblinks"][db][0]
                if db == "ChEBI":
                    annotation["chebi"] = self.data["dblinks"][db][0]
                if db == "MetaNetX":
                    annotation["metanetx.chemical"] = self.data["dblinks"][db][0]
                if db == "MetaCyc":
                    annotation["biocyc"] = self.data["dblinks"][db][0]
                if db == "ModelSeed":
                    annotation["seed.compound"] = self.data["dblinks"][db][0]
                if db == "HMDB":
                    annotation["hmdb"] = self.data["dblinks"][db][0]
        return annotation

    def get_seed_id(self):
        return self.data["compound_ref"].split("/")[-1]

    def get_reference(self, database):
        if "dblinks" in self.data and database in self.data["dblinks"]:
            if not len(self.data["dblinks"][database]) == 1:
                print("bad!", self.data["dblinks"][database])
            return self.data["dblinks"][database][0]
        return None

    def get_references(self, database):
        if "dblinks" in self.data and database in self.data["dblinks"]:
            if not len(self.data["dblinks"][database]) == 0:
                print("bad!", self.data["dblinks"][database])
            return self.data["dblinks"][database][0]
        return None

    def get_original_id(self):
        if (
            "string_attributes" in self.data
            and "original_id" in self.data["string_attributes"]
        ):
            return self.data["string_attributes"]["original_id"]
        return None

    def __str__(self):
        return self.id


class KBaseFBAModelReaction:
    def __init__(
        self, json=None, dblinks={}, name="reaction", id="rxn00000", model=None
    ):
        self.model = model

        if not json == None:
            self.data = json
        else:
            self.data = {
                "aliases": [],
                "dblinks": dblinks,
                "direction": direction,
                "edits": {},
                "gapfill_data": {},
                "id": id,
                "maxforflux": maxforflux,
                "maxrevflux": maxrevflux,
                "modelReactionProteins": [
                    {
                        "complex_ref": "~/template/complexes/name/cpx00700",
                        "modelReactionProteinSubunits": [
                            {
                                "feature_refs": ["~/genome/features/id/b3177"],
                                "note": "",
                                "optionalSubunit": 0,
                                "role": "Dihydropteroate synthase (EC 2.5.1.15)",
                                "triggering": 1,
                            }
                        ],
                        "note": "",
                        "source": "",
                    }
                ],
                "modelReactionReagents": modelReactionReagents,
                "modelcompartment_ref": "~/modelcompartments/id/c0",
                "name": name,
                "numerical_attributes": {},
                "probability": 0,
                "protons": 0,
                "reaction_ref": "~/template/reactions/id/" + reaction.id,
                "string_attributes": {},
            }

    @property
    def bounds(self):
        bounds = self.get_bounds()
        return (bounds[0], bounds[1])

    @property
    def compartments(self):
        return set(map(lambda m: m.compartment, self.metabolites))

    @property
    def metabolites(self):
        metabolites = {}
        stoichiometry = self.stoichiometry
        if not self.model == None:
            found = set()
            for cpd_id in stoichiometry:
                if self.model.metabolites.has_id(cpd_id):
                    metabolite = self.model.metabolites.get_by_id(cpd_id)
                    metabolites[metabolite] = stoichiometry[metabolite.id]
                    found.add(metabolite.id)

            # for metabolite in self.model.metabolites:
            #    if metabolite.id in stoichiometry.keys():
            #        found.add(metabolite.id)
            #        metabolites[metabolite] = stoichiometry[metabolite.id]

            missing = set(stoichiometry) - found
            if len(missing) > 0:
                logger.warning("undeclated metabolites: %s", missing)
        else:
            logger.warning("model not assigned")
        return metabolites

    @property
    def gene_reaction_rule(self):
        gpr = self.get_gpr()
        return self.get_gpr_string(gpr)

    @property
    def direction(self):
        lb, ub = self.get_reaction_constraints()
        if lb < 0 and ub > 0:
            return "="
        elif lb == 0 and ub > 0:
            return ">"
        elif lb < 0 and ub == 0:
            return "<"
        return "?"

    @property
    def annotation(self):
        annotation = {}
        if "dblinks" in self.data:
            for db in self.data["dblinks"]:
                if db == "BiGG":
                    annotation["bigg.reaction"] = self.data["dblinks"][db][0]
                if db == "LigandReaction":
                    annotation["kegg.reaction"] = self.data["dblinks"][db][0]
                if db == "MetaCyc":
                    annotation["biocyc"] = self.data["dblinks"][db][0]
                if db == "ModelSeedReaction":
                    annotation["seed.reaction"] = self.data["dblinks"][db][0]
        return annotation

    def get_reaction_constraints_from_direction(self):
        if "direction" in self.data:
            if self.data["direction"] == ">":
                return 0, 1000
            elif self.data["direction"] == "<":
                return -1000, 0
            else:
                return -1000, 1000
        return None, None

    def get_reaction_constraints(self):
        # clean this function !
        if "maxrevflux" in self.data and "maxforflux" in self.data:
            if (
                self.data["maxrevflux"] == 1000000
                and self.data["maxforflux"] == 1000000
                and "direction" in self.data
            ):
                return self.get_reaction_constraints_from_direction()

            return -1 * self.data["maxrevflux"], self.data["maxforflux"]
        return -1000, 1000

    def get_reference(self, database):
        if "dblinks" in self.data and database in self.data["dblinks"]:
            if not len(self.data["dblinks"][database]) == 1:
                print("bad!", self.data["dblinks"][database])
            return self.data["dblinks"][database][0]
        return None

    def get_references(self, database):
        if "dblinks" in self.data and database in self.data["dblinks"]:
            if not len(self.data["dblinks"][database]) == 0:
                print("bad!", self.data["dblinks"][database])
            return self.data["dblinks"][database][0]
        return None

    def get_original_id(self):
        if (
            "string_attributes" in self.data
            and "original_id" in self.data["string_attributes"]
        ):
            return self.data["string_attributes"]["original_id"]
        return None

    @property
    def id(self):
        return self.data["id"]

    @property
    def name(self):
        return self.data["name"]

    @property
    def stoichiometry(self):
        s = {}
        for o in self.data["modelReactionReagents"]:
            c_id = o["modelcompound_ref"].split("/")[-1]
            value = o["coefficient"]
            s[c_id] = value
        return s

    def get_bounds(self):
        if "maxrevflux" not in self.data or "maxforflux" not in self.data:
            import math
            from modelseedpy.core.msmodel import get_reaction_constraints_from_direction

            lb, ub = get_reaction_constraints_from_direction(self.data["direction"])
            return math.fabs(lb), math.fabs(ub), self.data["direction"]
        maxrevflux = self.data["maxrevflux"]
        maxforflux = self.data["maxforflux"]
        direction = "="
        if maxrevflux == 0 and maxforflux > 0:
            direction = ">"
        elif maxrevflux > 0 and maxforflux == 0:
            direction = "<"
        elif maxrevflux == 0 and maxforflux == 0:
            direction = "0"

        return maxrevflux, maxforflux, direction

    def get_gpr_string(self, gpr):
        ors = []
        for ands in gpr:
            a = []
            for g in ands:
                a.append(g)
            ors.append(" and ".join(a))
        gpr_string = "(" + (") or (".join(ors)) + ")"
        if gpr_string == "()":
            return ""
        # if gpr_string.startswith("(") and gpr_string.endswith(")"):
        #    gpr_string = gpr_string[1:-1].strip()
        return gpr_string

    def get_gpr(self):
        gpr = []
        for mrp in self.data["modelReactionProteins"]:
            # print(mrp.keys())
            gpr_and = set()
            for mrps in mrp["modelReactionProteinSubunits"]:
                # print(mrps.keys())
                for feature_ref in mrps["feature_refs"]:
                    gpr_and.add(get_id_from_ref(feature_ref))
            if len(gpr_and) > 0:
                gpr.append(gpr_and)
        return gpr

    def __str__(self):
        direction = self.direction
        op = "<?>"
        if direction == "=":
            op = "<=>"
        elif direction == ">":
            op = "-->"
        elif direction == "<":
            op = "<--"
        else:
            op = "<?>"

        eq = seed_coefficients_to_string(self.data["modelReactionReagents"], op)

        return "{}: {}".format(self.id, eq)


class KBaseFBAModel(KBaseObject):
    def __init__(self, data=None, info=None, args=None):
        super().__init__(data, info, args, "KBaseFBA.FBAModel")
        self.metabolites = DictList()
        model_compounds = []
        ids = set()
        for o in self.data["modelcompounds"]:
            if o["id"] not in ids:
                ids.add(o["id"])
                model_compounds.append(o)
        self.data["modelcompounds"] = model_compounds
        self.update_indexes()

    def update_indexes(self):
        if self.data is not None:
            self.metabolites += [
                KBaseFBAModelMetabolite(i) for i in self.get_metabolites()
            ]

    def get_compartments(self):
        return self.data["modelcompartments"]

    def get_reactions(self):
        if self.data == None or not "modelreactions" in self.data:
            return []
        return self.data["modelreactions"]

    def get_metabolites(self):
        if self.data == None or not "modelcompounds" in self.data:
            return []
        return self.data["modelcompounds"]

    def get_compartment(self, id):
        for c in self.get_compartments():
            if c["id"] == id:
                return c
        return None

    def get_metabolite(self, id):
        for m in self.get_metabolites():
            if m["id"] == id:
                return KBaseFBAModelMetabolite(m)
        return None

    def get_metabolite_degree(self, cpd_id):
        return len(self.find_reaction_by_compound_id(cpd_id))

    def build_peakstring(self, link, additional_peak_hash={}):
        peakstring_hash = dict()
        for met in self.modelcompounds:
            if hasattr(met, "dblinks"):
                if link in met.dblinks:
                    array = met.dblinks[link]
                    for form in array:
                        if form not in peakstring_hash:
                            peakstring_hash[form] = list()
                        peakstring_hash[form].append(met.id)
        for peak in additional_peak_hash:
            if peak not in peakstring_hash:
                peakstring_hash[peak] = list()
            for cpd in additional_peak_hash[peak]:
                if cpd not in peakstring_hash[peak]:
                    peakstring_hash[peak].append(cpd)
        print(len(peakstring_hash))
        peakstring = ""
        for form in peakstring_hash:
            peakstring += form + ":1"
            for cpd in peakstring_hash[form]:
                peakstring += ":" + cpd
            peakstring += ";"
        return peakstring

    @property
    def reactions(self):
        return [KBaseFBAModelReaction(i, model=self) for i in self.get_reactions()]

    def get_reaction(self, id):
        for r in self.get_reactions():
            if r["id"] == id:
                return KBaseFBAModelReaction(r)
        return None

    def add_reaction(self, rxn):
        # validate

        self.data["modelreactions"].append(rxn)
        return -1

    def add_metabolite(self, cpd, force=False):
        # validate
        if not force:
            # validate
            1

        self.data["modelcompounds"].append(cpd)
        return -1

    def find_compound_ids_by_compartment(self, id):
        ids = set()
        for m in self.get_metabolites():
            if m["modelcompartment_ref"].endswith(id):
                ids.add(m["id"])
        return ids

    def find_compound_id_from_oid(self, oid):
        for m in self.get_metabolites():
            sid = None
            if "string_attributes" in m and "original_id" in m["string_attributes"]:
                sid = m["string_attributes"]["original_id"]
            if sid == oid:
                return m["id"]
        return None

    def find_reaction_id_from_oid(self, oid):
        for r in self.get_reactions():
            sid = None
            if "string_attributes" in r and "original_id" in r["string_attributes"]:
                sid = r["string_attributes"]["original_id"]
            if sid == oid:
                return r["id"]
        return None

    def find_reaction_by_compound_id(self, modelcompound_id):
        rxn_list = []
        for modelreaction in self.data["modelreactions"]:
            # print(modelreaction.keys())
            contains = False
            for mrr in modelreaction["modelReactionReagents"]:
                if modelcompound_id in mrr["modelcompound_ref"]:
                    contains = True
            if contains:
                rxn_list.append(modelreaction)
        return rxn_list

    def delete_compartment(self, id, store=True):

        c = self.get_compartment(id)
        if not c == None:
            if store and not "modelcompartments_removed" in self.data:
                self.data["modelcompartments_removed"] = {}

            if store:
                self.data["modelcompartments_removed"][c["id"]] = c
            ids = self.find_compound_ids_by_compartment(id)
            print(c["id"], "removing compounds:", len(ids))
            self.delete_compounds(ids, store)
            compartments = [o for o in self.get_compartments() if not o["id"] == id]
            self.data["modelcompartments"] = compartments
        return c

    def delete_compounds(self, c_ids, store=True):
        metabolites = []

        if store and not "modelcompounds_removed" in self.data:
            self.data["modelcompounds_removed"] = {}
        for m in self.data["modelcompounds"]:
            if store and m["id"] in c_ids:
                self.data["modelcompounds_removed"][m["id"]] = m
            else:
                metabolites.append(m)

        self.data["modelcompounds"] = metabolites
        return metabolites

    def delete_reactions(self, r_ids, store=True):
        reactions = []

        if store and not "modelreactions_removed" in self.data:
            self.data["modelreactions_removed"] = {}
        for r in self.data["modelreactions"]:
            if store and r["id"] in r_ids:
                self.data["modelreactions_removed"][r["id"]] = r
            else:
                reactions.append(r)

        self.data["modelreactions"] = reactions
        return reactions

    def find_reactions_with_undeclared_metabolites(self):
        compounds = set()
        for m in self.data["modelcompounds"]:
            compounds.add(m["id"])
        result = set()
        for r in self.data["modelreactions"]:
            for reagents in r["modelReactionReagents"]:
                c_id = reagents["modelcompound_ref"].split("/")[-1]
                if not c_id in compounds:
                    result.add(r["id"])

        return result

    def generate_cpd_rename(self, database, dblinks):
        result = {}
        for m in self.get_metabolites():
            if m["id"] in dblinks and database in dblinks[m["id"]]:
                result[m["id"]] = dblinks[m["id"]][database]
        return result

    def generate_rxn_rename(self, database, dblinks):
        result = {}
        for r in self.get_reactions():
            if r["id"] in dblinks and database in dblinks[r["id"]]:
                result[r["id"]] = dblinks[r["id"]][database]
        return result

    def clean_enzymes_from_metabolites(self, store=True):
        to_delete = set()
        for m in self.data["modelcompounds"]:
            if (
                m["id"].startswith("E-")
                or m["id"].startswith("Cx-")
                or m["id"].startswith("E_")
                or m["id"].startswith("Cx_")
            ):
                to_delete.add(m["id"])
        self.delete_compounds(to_delete, store=store)
        return to_delete

    def clean_reactions_without_genes(self, store=True):
        if store:
            to_delete = [
                r for r in self.get_reactions() if len(r["modelReactionProteins"]) == 0
            ]
            for o in to_delete:
                self.data["modelreactions_removed"][o["id"]] = o
        reactions = [
            r for r in self.get_reactions() if len(r["modelReactionProteins"]) > 0
        ]
        self.data["modelreactions"] = reactions

    def clean_orphan_metabolites(self, store=True):
        orphans = [
            o
            for o in self.get_metabolites()
            if self.get_metabolite_degree(o["id"]) == 0
        ]
        orphans_ids = [o["id"] for o in orphans]
        compounds = [o for o in self.get_metabolites() if not o["id"] in orphans_ids]

        if store:
            # store orphans
            1

        self.data["modelcompounds"] = compounds

    def rename_compound_ids(self, old_to_new_id):
        for m in self.get_metabolites():
            id = m["id"]
            if id in old_to_new_id:
                m["id"] = old_to_new_id[id]
                # print(old_to_new_id[id], m['id'])
        self.swap_reaction_reagent_compound_ids(old_to_new_id)

    def rename_reaction_ids(self, old_to_new_id):
        for r in self.get_reactions():
            id = r["id"]
            if id in old_to_new_id:
                r["id"] = old_to_new_id[id]
                # print(old_to_new_id[id], m['id'])

    def update_compartment(self, id, new_id, index):
        c = self.get_compartment(id)
        if not c == None:
            cpd_ids = self.find_compound_ids_by_compartment(id)
            cpd_renames = {}
            for cpd_id in cpd_ids:
                cpd = self.get_metabolite(cpd_id)
                cpd_id_tokens = cpd.data["id"].split("_")
                if cpd_id_tokens[-1] == id:
                    cpd_id_tokens[-1] = new_id + str(index)
                    cpd_renames[cpd.data["id"]] = "_".join(cpd_id_tokens)
                cpd.data["id"] = "_".join(cpd_id_tokens)
                cpd.data["modelcompartment_ref"] = (
                    "~/modelcompartments/id/" + new_id + str(index)
                )
            self.swap_reaction_reagent_compound_ids(cpd_renames)
            c["compartmentIndex"] = index
            c["id"] = new_id + str(index)
            c["compartment_ref"] = "~/template/compartments/id/" + new_id
        else:
            print("not found", id)
        return c

    def swap_reaction_reagent_compound_ids(self, old_to_new_id):
        for r in self.data["modelreactions"]:
            for reagent in r["modelReactionReagents"]:
                c_id = reagent["modelcompound_ref"].split("/")[-1]
                if c_id in old_to_new_id:
                    reagent["modelcompound_ref"] = (
                        "~/modelcompounds/id/" + old_to_new_id[c_id]
                    )

    # merge_id does nothing atm
    def merge_compounds(self, id1, id2, keep=None, merge_id=None):
        m1 = self.get_metabolite(id1)
        m2 = self.get_metabolite(id2)
        # print(keep, id1, id2)
        if m1 == None or m2 == None:
            return None

        m_merge = {}
        for k in m1.data:
            if not k in m_merge:
                m_merge[k] = None
        for k in m2.data:
            if not k in m_merge:
                m_merge[k] = None

        for k in m_merge:
            if k in m1.data and k in m2.data:
                v1 = m1.data[k]
                v2 = m2.data[k]
                if v1 == v2:
                    m_merge[k] = v1
                elif not keep == None and keep == id1:
                    m_merge[k] = v1
                elif not keep == None and keep == id2:
                    m_merge[k] = v2
                else:
                    print("not sure how to merge:", k, m1.data[k], m2.data[k])
            elif k in m1.data:
                m_merge[k] = m1.data[k]
            else:
                m_merge[k] = m2.data[k]

        for r in self.data["modelreactions"]:
            for reagent in r["modelReactionReagents"]:
                c_id = reagent["modelcompound_ref"].split("/")[-1]
                if c_id == id1 or c_id == id2:
                    # print(reagent)
                    # print(c_id, m_merge['id'], '~/modelcompounds/id/' + m_merge['id'])
                    reagent["modelcompound_ref"] = (
                        "~/modelcompounds/id/" + m_merge["id"]
                    )

        if not keep == None and keep == id1:
            self.delete_compounds([id2])
            m1.data = m_merge
        elif not keep == None and keep == id2:
            self.delete_compounds([id1])
            m2.data = m_merge
        else:
            self.delete_compounds([id1, id2])
            self.data["modelcompounds"].append(m_merge)

        return m_merge


def get_compartment_id(modelcompound, simple=False):
    modelcompartment_ref = modelcompound["modelcompartment_ref"]
    compartment = get_id_from_ref(modelcompartment_ref)
    if simple:
        return compartment[0]
    return compartment


def get_cpd_annotation(dblinks):
    annotation = {}

    for db in dblinks:
        if db == "BiGG2":
            annotation["bigg.metabolite"] = dblinks[db][0]
        if db == "LigandCompound":
            annotation["kegg.compound"] = dblinks[db][0]
        if db == "ChEBI":
            annotation["chebi"] = dblinks[db][0]
        if db == "MetaNetX":
            annotation["metanetx.chemical"] = dblinks[db][0]
        if db == "MetaCyc":
            annotation["biocyc"] = dblinks[db][0]
        if db == "ModelSeed":
            annotation["seed.compound"] = dblinks[db][0]
        if db == "HMDB":
            annotation["hmdb"] = dblinks[db][0]
    return annotation


def get_rxn_annotation(dblinks):
    annotation = {}
    # print(dblinks)
    for db in dblinks:
        if db == "BiGG":
            annotation["bigg.reaction"] = dblinks[db][0]
        if db == "LigandReaction":
            annotation["kegg.reaction"] = dblinks[db][0]
        if db == "MetaCyc":
            annotation["biocyc"] = dblinks[db][0]
        if db == "ModelSeedReaction":
            annotation["seed.reaction"] = dblinks[db][0]
    return annotation


def build_gene_id(str):
    if str.startswith("G_"):
        return str[2:]
    return str


def build_cpd_id(str):
    if str.startswith("M_"):
        return str[2:]
    if str.startswith("M-"):
        return str[2:]
    return str


def build_rxn_id(str):
    if str.startswith("R_"):
        return str[2:]
    if str.startswith("R-"):
        return str[2:]
    return str


def get_id_from_ref(str):
    id = str.split("/")[-1]
    id = id.replace("|", "")
    return id


def get_genes(gpr):
    genes = set()
    for s in gpr:
        genes |= s
    return genes


def get_gpr_string(gpr):
    ors = []
    for ands in gpr:
        a = []
        for g in ands:
            a.append(g)
        ors.append(" and ".join(a))
    gpr_string = "(" + (") or (".join(ors)) + ")"
    if gpr_string == "()":
        return ""
    # if gpr_string.startswith("(") and gpr_string.endswith(")"):
    #    gpr_string = gpr_string[1:-1].strip()
    return gpr_string


def get_gpr(mr):
    gpr = []
    for mrp in mr["modelReactionProteins"]:
        # print(mrp.keys())
        gpr_and = set()
        for mrps in mrp["modelReactionProteinSubunits"]:
            # print(mrps.keys())
            for feature_ref in mrps["feature_refs"]:
                gpr_and.add(get_id_from_ref(feature_ref))
        if len(gpr_and) > 0:
            gpr.append(gpr_and)
    return gpr
