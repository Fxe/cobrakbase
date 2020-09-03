import logging
import copy
from cobra.core import Reaction, Gene
from cobra.util.solver import linear_reaction_coefficients
from cobrakbase.core.kbasefba import ModelCompound, ModelReaction, Biomass, FBAModel

logger = logging.getLogger(__name__)


def _build_gene_id(s):
    if s.startswith("G_"):
        return s[2:]
    return s


class FBAModelBuilder:

    def __init__(self, data, info, args=None, auto_exchange='e0'):
        self.data = data
        self.info = info
        self.args = args
        self.metabolites = {}
        self.reactions = {}
        self.genes = {}
        self.gene_annotation = {}

        self.auto_exchange = auto_exchange

        self.biomass_reactions = set()

        self.sink_compounds = set()
        self.demand_compounds = set()
        self.exchange_compounds = set()

        self.SBO_ANNOTATION = "sbo"
        self.COBRA_0_BOUND = 0
        self.COBRA_DEFAULT_LB = -1000
        self.COBRA_DEFAULT_UB = 1000

        self.media_const = {}

    @staticmethod
    def from_kbase_json(data, info, args=None, auto_exchange='e0'):
        b = FBAModelBuilder(copy.deepcopy(data), info, args)
        b.with_sink("cpd02701_c0") \
            .with_sink("cpd11416_c0") \
            .with_sink("cpd15302_c0") \
            .with_sink("cpd11416_c0")
        b.auto_exchange = auto_exchange
        return b

    def with_exchange(self, compound_id):
        self.exchange_compounds.add(compound_id)
        return self

    def with_sink(self, compound_id):
        self.sink_compounds.add(compound_id)
        return self

    def with_demand(self, compound_id):
        self.demand_compounds.add(compound_id)
        return self

    def convert_modelcompound(self, data, bigg=False):
        mc_id = data['id']

        annotation = {}

        # id = build_cpd_id(mc_id)

        # if bigg and "bigg.metabolite" in annotation:
        #    id = annotation["bigg.metabolite"] + "_" + compartment
        #        #print(id)

        met = ModelCompound(data)

        # simple chemical - Simple, non-repetitive chemical entity.
        met.annotation[self.SBO_ANNOTATION] = "SBO:0000247"
        if met.id.startswith('cpd'):
            met.annotation["seed.compound"] = met.compound_id
        met.annotation.update(annotation)
        return met

    def convert_modelreaction(self, data, bigg=False):
        mr_id = data['id']
        annotation = {}  # reaction.annotation

        # id = build_rxn_id(mr_id)
        # if bigg and "bigg.reaction" in annotation:
        #    id = annotation["bigg.reaction"]

        # gpr = reaction.get_gpr()

        reaction = ModelReaction(data)
        reaction.annotation[self.SBO_ANNOTATION] = "SBO:0000176"  # biochemical reaction
        reaction.annotation.update(annotation)

        if reaction.id.startswith('rxn'):
            reaction.annotation["seed.reaction"] = reaction.id.split("_")[0]

        reaction.add_metabolites(self.convert_modelreaction_stoichiometry(data))

        # reaction.gene_reaction_rule = reaction.gene_reaction_rule

        for gene in reaction.genes:
            self.genes[gene.id] = gene.id

        return reaction

    def convert_biomass_to_reaction(self, biomass):
        # mr_id = biomass['id'] + "_biomass"
        # name = biomass['name']
        object_stoichiometry = {}
        for biomasscompound in biomass['biomasscompounds']:
            coefficient = biomasscompound['coefficient']
            metabolite_id = biomasscompound['modelcompound_ref'].split('/')[-1]

            if metabolite_id in self.metabolites:
                object_stoichiometry[self.metabolites[metabolite_id]] = coefficient
            else:
                logger.warning('[%s] undeclared biomass species: %s', biomass['id'], metabolite_id)

        reaction = Biomass(biomass)
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
        for o in model_reaction['modelReactionReagents']:
            compound_id = o['modelcompound_ref'].split('/')[-1]
            if compound_id in self.metabolites:
                object_stoichiometry[self.metabolites[compound_id]] = o['coefficient']
            else:
                logger.warning('[%s] undeclared species: %s', model_reaction['id'], compound_id)
        return object_stoichiometry

    def build_drain_from_metabolite_id(self, cpd_id, lower_bound, upper_bound,
                                       prefix='EX_', prefix_name='Exchange for ', sbo='SBO:0000627'):
        if cpd_id in self.metabolites:
            id = prefix + cpd_id
            cobra_metabolite = self.metabolites[cpd_id]
            object_stoichiometry = {cobra_metabolite: -1}
            drain_reaction = Reaction(id=id,
                                      name=prefix_name + cobra_metabolite.name,
                                      lower_bound=lower_bound,
                                      upper_bound=upper_bound)
            drain_reaction.add_metabolites(object_stoichiometry)
            #  exchange reaction - ... provide matter influx or efflux to a model, for example to replenish a
            # metabolic network with raw materials ...
            drain_reaction.annotation[self.SBO_ANNOTATION] = sbo

            return drain_reaction

    def build(self):
        for modelcompound in self.data['modelcompounds']:
            metabolite = self.convert_modelcompound(modelcompound)
            self.metabolites[metabolite.id] = metabolite
            if metabolite.compartment == self.auto_exchange:
                logger.debug('Add Exchange: [%s]', metabolite.id)
                self.exchange_compounds.add(metabolite.id)

        logger.info('metabolites %d', len(self.metabolites))

        for modelreaction in self.data['modelreactions']:
            reaction = self.convert_modelreaction(modelreaction)
            self.reactions[reaction.id] = reaction

        logger.info('reactions %d', len(self.reactions))

        model = FBAModel(copy.deepcopy(self.data), self.info, self.args)

        for gene_id in self.genes:
            gene = Gene(id=_build_gene_id(gene_id), name=gene_id)
            gene.annotation[self.SBO_ANNOTATION] = "SBO:0000243"
            if gene_id in self.gene_annotation:
                gene.annotation.update(self.gene_annotation[gene_id])
            model.genes.append(gene)

        for biomass in self.data['biomasses']:
            reaction = self.convert_biomass_to_reaction(biomass)
            reaction.lower_bound = self.COBRA_0_BOUND
            reaction.upper_bound = self.COBRA_DEFAULT_UB
            self.reactions[reaction.id] = reaction
            self.biomass_reactions.add(reaction.id)

        for cpd_id in self.exchange_compounds:
            lower_bound = self.COBRA_DEFAULT_LB if len(self.media_const) == 0 else self.COBRA_0_BOUND
            upper_bound = self.COBRA_DEFAULT_UB
            if cpd_id in self.media_const:
                lower_bound, upper_bound = self.media_const[cpd_id]
            drain_reaction = self.build_drain_from_metabolite_id(cpd_id, lower_bound, upper_bound)
            self.reactions[drain_reaction.id] = drain_reaction
            # self.add_reaction(drain_reaction)
            logger.debug('created exchange for [%s]: %s', cpd_id, drain_reaction)
        for cpd_id in self.demand_compounds:
            drain_reaction = self.build_drain_from_metabolite_id(cpd_id, self.COBRA_0_BOUND, self.COBRA_DEFAULT_UB,
                                                                 "DM_", "Demand for ")
            self.reactions[drain_reaction.id] = drain_reaction
            # self.add_reaction(drain_reaction)
            logger.debug('created demand for [%s]: %s', cpd_id, drain_reaction)
        for cpd_id in self.sink_compounds:
            drain_reaction = self.build_drain_from_metabolite_id(cpd_id, self.COBRA_0_BOUND, self.COBRA_DEFAULT_UB,
                                                                 "SK_", "Sink for ")
            self.reactions[drain_reaction.id] = drain_reaction
            # self.add_reaction(drain_reaction)
            logger.debug('created sink for [%s]: %s', cpd_id, drain_reaction)

        model.add_metabolites(self.metabolites.values())
        model.add_reactions(self.reactions.values())

        if len(self.biomass_reactions) > 0:
            default_biomass = list(self.biomass_reactions)[0]
            logger.info('Default biomass: [%s]', default_biomass)
            model.objective = default_biomass
            linear_reaction_coefficients(model)

        return model