import logging
import json
import copy
from cobra.core import Reaction, Gene, Group
from cobra.util.solver import linear_reaction_coefficients
from cobrakbase.kbase_object_info import KBaseObjectInfo
from cobrakbase.core.kbasefba.fbamodel import ModelCompartment
from cobrakbase.core.kbasefba import ModelCompound, ModelReaction, Biomass, FBAModel

logger = logging.getLogger(__name__)


def _build_gene_id(s):
    if s.startswith("G_"):
        return s[2:]
    return s


class FBAModelBuilder:
    def __init__(self, data, info=None, args=None, auto_exchange="e0"):
        self.data = data
        self.info = info
        self.args = args
        self.compartments = {}
        self.metabolites_remap = {}
        self.metabolites = {}
        self.reactions = {}
        self.genes = {}
        self.gene_annotation = {}

        self.auto_exchange = auto_exchange

        self.biomass_reactions = set()

        self.sink_compounds = {}
        self.demand_compounds = {}
        self.exchange_compounds = set()

        self.SBO_ANNOTATION = "sbo"
        self.COBRA_0_BOUND = 0
        self.COBRA_DEFAULT_LB = -1000
        self.COBRA_DEFAULT_UB = 1000

        self.media_const = {}

        if self.info is None:
            self.info = KBaseObjectInfo(object_type="KBaseFBA.FBAModel")

    @staticmethod
    def from_kbase_json(data, info, args=None, auto_exchange="e0"):
        b = FBAModelBuilder(copy.deepcopy(data), info, args)

        if "drain_list" not in data:
            from modelseedpy.core.msbuilder import DEFAULT_SINKS

            for template_cpd_id in DEFAULT_SINKS:
                b.with_sink(template_cpd_id + "0", DEFAULT_SINKS[template_cpd_id])
        else:
            for cpd_id in data["drain_list"]:
                lb, ub = data["drain_list"][cpd_id]
                if ub > 0:
                    b.with_sink(cpd_id, ub)
                if lb < 0:
                    b.with_demand(cpd_id, lb)

        b.auto_exchange = auto_exchange
        return b

    def with_exchange(self, compound_id):
        self.exchange_compounds.add(compound_id)
        return self

    def with_sink(self, compound_id, upper_bound):
        self.sink_compounds[compound_id] = upper_bound
        return self

    def with_demand(self, compound_id, lower_bound):
        self.demand_compounds[compound_id] = lower_bound
        return self

    def convert_modelcompound(self, data, bigg=False):
        mc_id = data["id"]

        annotation = {}

        # id = build_cpd_id(mc_id)

        # if bigg and "bigg.metabolite" in annotation:
        #    id = annotation["bigg.metabolite"] + "_" + compartment
        #        #print(id)

        met = ModelCompound.from_json(data)
        self.metabolites_remap[data["id"]] = met.id

        # simple chemical - Simple, non-repetitive chemical entity.
        met.annotation[self.SBO_ANNOTATION] = "SBO:0000247"
        if met.id.startswith("cpd"):
            met.annotation["seed.compound"] = met.compound_id
        met.annotation.update(annotation)
        return met

    def convert_modelreaction(self, data, bigg=False):
        mr_id = data["id"]
        annotation = {}  # reaction.annotation

        # id = build_rxn_id(mr_id)
        # if bigg and "bigg.reaction" in annotation:
        #    id = annotation["bigg.reaction"]

        # gpr = reaction.get_gpr()

        reaction = ModelReaction.from_json(data)
        reaction.annotation[self.SBO_ANNOTATION] = "SBO:0000176"  # biochemical reaction
        reaction.annotation.update(annotation)

        if reaction.id.startswith("rxn"):
            reaction.annotation["seed.reaction"] = reaction.id.split("_")[0]

        reaction.add_metabolites(self.convert_modelreaction_stoichiometry(data))

        # reaction.gene_reaction_rule = reaction.gene_reaction_rule

        for gene in reaction.genes:
            self.genes[gene.id] = gene.id

        return reaction

    def convert_biomass_to_reaction(self, kbase_biomass_dict):
        # mr_id = biomass['id'] + "_biomass"
        # name = biomass['name']
        object_stoichiometry = {}
        for o in kbase_biomass_dict["biomasscompounds"]:
            coefficient = o["coefficient"]
            metabolite_id = o["modelcompound_ref"].split("/")[-1]

            if metabolite_id in self.metabolites_remap:
                mapped_id = self.metabolites_remap[metabolite_id]
                object_stoichiometry[self.metabolites[mapped_id]] = coefficient
            else:
                logger.warning(
                    "[%s] undeclared biomass species: %s",
                    kbase_biomass_dict["id"],
                    metabolite_id,
                )

        reaction = Biomass.from_json(kbase_biomass_dict)
        objective_id = reaction.id
        reaction.add_metabolites(object_stoichiometry)
        # SBO:0000629 [biomass production]
        # Biomass production, often represented 'R_BIOMASS_', is usually
        # the optimization target reaction of constraint-based models ...
        reaction.annotation[self.SBO_ANNOTATION] = "SBO:0000629"
        return reaction

    def with_media(self, media):
        self.media_const = media.get_media_constraints()
        return self

    def with_genome(self, genome):
        self.gene_annotation = genome.read_genome_aliases()
        return self

    def convert_modelreaction_stoichiometry(self, model_reaction):
        object_stoichiometry = {}
        for o in model_reaction["modelReactionReagents"]:
            compound_id = o["modelcompound_ref"].split("/")[-1]
            if compound_id in self.metabolites_remap:
                mapped_id = self.metabolites_remap[compound_id]
                object_stoichiometry[self.metabolites[mapped_id]] = o["coefficient"]
            else:
                logger.warning(
                    "[%s] undeclared species: %s", model_reaction["id"], compound_id
                )
        return object_stoichiometry

    def build_drain_from_metabolite_id(
        self,
        cpd_id,
        lower_bound,
        upper_bound,
        prefix="EX_",
        prefix_name="Exchange for ",
        sbo="SBO:0000627",
    ):
        if cpd_id in self.metabolites:
            id = prefix + cpd_id
            cobra_metabolite = self.metabolites[cpd_id]
            object_stoichiometry = {cobra_metabolite: -1}
            drain_reaction = Reaction(
                id=id,
                name=prefix_name + cobra_metabolite.name,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
            )
            drain_reaction.add_metabolites(object_stoichiometry)
            #  exchange reaction - ... provide matter influx or efflux to a model, for example to replenish a
            # metabolic network with raw materials ...
            drain_reaction.annotation[self.SBO_ANNOTATION] = sbo

            return drain_reaction

    def build(self):
        cmp_notes = {}
        for cmp_data in self.data["modelcompartments"]:
            cmp = ModelCompartment.from_json(cmp_data)
            if cmp.id not in self.compartments:
                self.compartments[cmp.id] = cmp
                cmp_notes[cmp.get_sbml_notes_key()] = cmp.get_sbml_notes_data()
            else:
                logger.warning("cmp %s is found twice? ignoring duplicate", cmp.id)

        for mc in self.data["modelcompounds"]:
            metabolite = self.convert_modelcompound(mc)
            self.metabolites[metabolite.id] = metabolite
            if metabolite.compartment == self.auto_exchange:
                logger.debug("Add Exchange: [%s]", metabolite.id)
                self.exchange_compounds.add(metabolite.id)

        logger.info("metabolites %d", len(self.metabolites))

        complex_groups = {}
        for modelreaction in self.data["modelreactions"]:
            reaction = self.convert_modelreaction(modelreaction)
            if reaction.id not in self.reactions:
                self.reactions[reaction.id] = reaction
            else:
                logger.warning(f"duplicate reaction ID: {reaction.id}")

            for complex_data in modelreaction["modelReactionProteins"]:
                complex_id = complex_data["complex_ref"].split("/")[-1]
                notes = {}
                if complex_id not in complex_groups:
                    complex_group = Group(complex_id)
                    notes["complex_note"] = complex_data["note"]
                    notes["complex_source"] = complex_data["source"]
                    for u in complex_data["modelReactionProteinSubunits"]:
                        role_id = u["role"]
                        features = ";".join(
                            {x.split("/")[-1] for x in u["feature_refs"]}
                        )
                        notes[f"complex_subunit_features_{role_id}"] = features
                        notes[f"complex_subunit_note_{role_id}"] = u["note"]
                        notes[f"complex_subunit_optional_{role_id}"] = u[
                            "optionalSubunit"
                        ]
                        notes[f"complex_subunit_triggering_{role_id}"] = u["triggering"]
                    complex_group.notes = notes
                    complex_groups[complex_group.id] = complex_group

        logger.info("reactions %d", len(self.reactions))

        data_copy = copy.deepcopy(self.data)
        del data_copy["biomasses"]
        del data_copy["modelcompounds"]
        del data_copy["modelreactions"]
        del data_copy["modelcompartments"]

        model = FBAModel(data_copy, self.info, self.args)
        model.genome_ref = self.data["genome_ref"]
        model.model_type = self.data["type"]
        model.source = self.data["source"]
        model.source_id = self.data["source_id"]
        model.gapfillings = self.data["gapfillings"]
        model.gapgens = self.data["gapgens"]
        if "attributes" in self.data:
            model.computed_attributes = self.data["attributes"]

        templates = []
        if "template_refs" in self.data:
            templates = [x for x in self.data["template_refs"]]
        if "template_ref" in self.data and self.data["template_ref"] not in templates:
            templates.append(self.data["template_ref"])
        if len(templates) > 0:
            model.notes["kbase_template_refs"] = ";".join(templates)

        for gene_id in self.genes:
            gene = Gene(id=_build_gene_id(gene_id), name=gene_id)
            gene.annotation[self.SBO_ANNOTATION] = "SBO:0000243"
            if gene_id in self.gene_annotation:
                gene.annotation.update(self.gene_annotation[gene_id])
            model.genes.append(gene)

        for biomass in self.data["biomasses"]:
            reaction = self.convert_biomass_to_reaction(biomass)
            reaction.lower_bound = self.COBRA_0_BOUND
            reaction.upper_bound = self.COBRA_DEFAULT_UB
            if reaction.id not in self.reactions:
                self.reactions[reaction.id] = reaction
                self.biomass_reactions.add(reaction.id)
            else:
                logger.warning(f"duplicate reaction ID: {reaction.id}")

        for cpd_id in self.exchange_compounds:
            if cpd_id in self.metabolites:
                lower_bound = (
                    self.COBRA_DEFAULT_LB
                    if len(self.media_const) == 0
                    else self.COBRA_0_BOUND
                )
                upper_bound = self.COBRA_DEFAULT_UB
                if cpd_id in self.media_const:
                    lower_bound, upper_bound = self.media_const[cpd_id]
                drain_reaction = self.build_drain_from_metabolite_id(
                    cpd_id, lower_bound, upper_bound
                )
                self.reactions[drain_reaction.id] = drain_reaction
                # self.add_reaction(drain_reaction)
                logger.debug("created exchange for [%s]: %s", cpd_id, drain_reaction)
            else:
                logger.debug("unable to add exchange for [%s]: not found", cpd_id)

        for cpd_id, v in self.demand_compounds.items():
            if cpd_id in self.metabolites:
                drain_reaction = self.build_drain_from_metabolite_id(
                    cpd_id,
                    v,
                    self.COBRA_0_BOUND,
                    "DM_",
                    "Demand for ",
                    sbo="SBO:0000628"
                )
                self.reactions[drain_reaction.id] = drain_reaction
                # self.add_reaction(drain_reaction)
                logger.debug("created demand for [%s]: %s", cpd_id, drain_reaction)
            else:
                logger.debug("unable to add demand for [%s]: not found", cpd_id)
        for cpd_id, v in self.sink_compounds.items():
            if cpd_id in self.metabolites:
                drain_reaction = self.build_drain_from_metabolite_id(
                    cpd_id,
                    self.COBRA_0_BOUND,
                    v,
                    "SK_",
                    "Sink for ",
                    sbo="SBO:0000632"
                )
                self.reactions[drain_reaction.id] = drain_reaction
                # self.add_reaction(drain_reaction)
                logger.debug("created sink for [%s]: %s", cpd_id, drain_reaction)
            else:
                logger.debug("unable to add sink for [%s]: not found", cpd_id)

        model.compartments = self.compartments
        model.add_metabolites(list(self.metabolites.values()))
        model.add_reactions(list(self.reactions.values()))
        model.add_groups(list(complex_groups.values()))
        model.notes.update(cmp_notes)

        if len(self.biomass_reactions) > 0:
            default_biomass = list(self.biomass_reactions)[0]
            logger.info("Default biomass: [%s]", default_biomass)
            model.objective = default_biomass
            linear_reaction_coefficients(model)

        return model
