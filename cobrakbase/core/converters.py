import logging
from cobra.core import Gene, Metabolite, Model, Reaction
from cobra.util.solver import linear_reaction_coefficients

logger = logging.getLogger(__name__)

def get_id_from_ref(str, stok='/'):
    return str.split(stok)[-1]

def build_gene_id(str):
    if str.startswith("G_"):
        return str[2:]
    return str

def build_cpd_id(str):
    if str.startswith("M_"):
        str = str[2:]
    elif str.startswith("M-"):
        str = str[2:]
    str_fix = str
    if '-' in str_fix:
        str_fix = str_fix.replace('-', '__DASH__')
    if not str == str_fix:
        logger.debug('[Species] rename: [%s] -> [%s]', str, str_fix)
    return str

def build_rxn_id(str):
    if str.startswith("R_"):
        str = str[2:]
    elif str.startswith("R-"):
        str = str[2:]
    str_fix = str
    if '-' in str_fix:
        str_fix = str_fix.replace('-', '__DASH__')
    if not str == str_fix:
        logger.debug('[Reaction] rename: [%s] -> [%s]', str, str_fix)
    return str_fix

class KBaseFBAModelToCobraBuilder():
    
    def __init__(self, fbamodel, media_const = {}, auto_sink = ["cpd02701_c0", "cpd11416_c0", "cpd15302_c0", "cpd11416_c0"]):
        self.fbamodel = fbamodel
        self.media_const = media_const
        
        self.SBO_ANNOTATION = "sbo"
        self.auto_sink = auto_sink
        self.auto_exchange = "e0"
        
        self.metabolites = {}
        self.metabolites_remap = {} #change of ids
        self.reactions = {}
        self.genes = {}
        self.biomass_reactions = set()
        
        self.sink_compounds = set()
        self.demand_compounds = set()
        self.exchange_compounds = set()
        
        self.COBRA_0_BOUND = 0
        self.COBRA_DEFAULT_LB = -1000
        self.COBRA_DEFAULT_UB = 1000
        
        self.reaction_copy_number = {}
        self.gene_annotation = {}
        
    def with_media(self, media):
        self.media_const = media.get_media_constraints()
        return self
    
    def with_genome(self, genome):
        self.gene_annotation = genome.read_genome_aliases()
        return self
    
    def with_seed_annoation(self, modelseed):
        
        return self
        
    def add_reaction(self, cobra_reaction, copy_duplicate = True):
        if not cobra_reaction.id in self.reactions:
            self.reactions[cobra_reaction.id] = cobra_reaction
        else:
            logger.warning('duplicate reaction: %s', cobra_reaction.id)
            if copy_duplicate:
                if not cobra_reaction.id in self.reaction_copy_number:
                    self.reaction_copy_number[cobra_reaction.id] = 1
                    
                copy_id = cobra_reaction.id + "_copy" + str(self.reaction_copy_number[cobra_reaction.id])
                
                logger.warning('copy reaction: [%s] -> [%s]', cobra_reaction.id, copy_id)
                
                self.reaction_copy_number[cobra_reaction.id] += 1
                cobra_reaction.id = copy_id
                self.reactions[cobra_reaction.id] = cobra_reaction
            else:
                return None
            
        return cobra_reaction
    
    def convert_modelcompartment(self, compartment, bigg=False):
        return None
    
    def convert_modelreaction_stoichiometry(self, reaction):
        object_stoichiometry = {}
        s = reaction.stoichiometry
        for metabolite_id in s:
            if metabolite_id in self.metabolites_remap:
                object_stoichiometry[self.metabolites[self.metabolites_remap[metabolite_id]]] = s[metabolite_id]
            else:
                logger.warning('[%s] undeclared species: %s', reaction.id, metabolite_id)
        return object_stoichiometry
    
    def convert_biomass_to_reaction(self, biomass):
        mr_id = biomass['id'] + "_biomass"
        name = biomass['name']
        object_stoichiometry = {}
        for biomasscompound in biomass['biomasscompounds']:
            coefficient = biomasscompound['coefficient']
            modelcompound_ref = biomasscompound['modelcompound_ref']
            metabolite_id = get_id_from_ref(modelcompound_ref)
            
            if metabolite_id in self.metabolites_remap:
                object_stoichiometry[self.metabolites[self.metabolites_remap[metabolite_id]]] = coefficient
            else:
                logger.warning('[%s] undeclared biomass species: %s', mr_id, metabolite_id)
                
        reaction = Reaction(id=build_rxn_id(mr_id), name=name, lower_bound=self.COBRA_0_BOUND, upper_bound=self.COBRA_DEFAULT_UB)
        objective_id = reaction.id
        reaction.add_metabolites(object_stoichiometry)
        #SBO:0000629 [biomass production]
        #Biomass production, often represented 'R_BIOMASS_', is usually the optimization target reaction of constraint-based models ...
        reaction.annotation[self.SBO_ANNOTATION] = "SBO:0000629" 
        return reaction
    
    def convert_modelreaction(self, reaction, bigg=False):
        mr_id = reaction.id
        name = reaction.name
        annotation = reaction.annotation
        lower_bound, upper_bound = reaction.get_reaction_constraints()
        
        id = build_rxn_id(mr_id)
        if bigg and "bigg.reaction" in annotation:
            id = annotation["bigg.reaction"]
        
        gpr = reaction.get_gpr()
        
        cobra_reaction = Reaction(id, 
                                  name=name, 
                                  lower_bound=lower_bound, 
                                  upper_bound=upper_bound)
        cobra_reaction.annotation[self.SBO_ANNOTATION] = "SBO:0000176" #biochemical reaction
        cobra_reaction.annotation.update(annotation)
        
        if id.startswith('rxn'):
            cobra_reaction.annotation["seed.reaction"] = id.split("_")[0]
        
        cobra_reaction.add_metabolites(self.convert_modelreaction_stoichiometry(reaction))
        
        cobra_reaction.gene_reaction_rule = reaction.gene_reaction_rule
        
        for genes in gpr:
            for gene in genes:
                if not gene in self.genes:
                    self.genes[gene] = gene
        
        return cobra_reaction
    
    def convert_modelcompound(self, metabolite, bigg=False):
        formula = metabolite.formula
        name = metabolite.name
        charge = metabolite.charge
        mc_id = metabolite.id
        compartment = metabolite.compartment
        annotation = metabolite.annotation
        logger.debug('%s[%s]: %s %s (%d)', mc_id, compartment, name, formula, charge)
        
        id = build_cpd_id(mc_id)
        
        if bigg and "bigg.metabolite" in annotation:
            id = annotation["bigg.metabolite"] + "_" + compartment
                #print(id)

        met = Metabolite(id, 
                         formula=formula, 
                         name=name, 
                         charge=charge, 
                         compartment=compartment)
        
        met.annotation[self.SBO_ANNOTATION] = "SBO:0000247" #simple chemical - Simple, non-repetitive chemical entity.
        if id.startswith('cpd'):
            met.annotation["seed.compound"] = id.split("_")[0]
        met.annotation.update(annotation)
        return met
    
    def build_drain_from_metabolite_id(self, cpd_id, lower_bound, upper_bound, 
                                       prefix = 'EX_', prefix_name = 'Exchange for ', sbo = 'SBO:0000627'):
        if cpd_id in self.metabolites:
            id = prefix + cpd_id
            cobra_metabolite = self.metabolites[cpd_id]
            object_stoichiometry = {cobra_metabolite : -1}
            drain_reaction = Reaction(id=id, 
                                      name= prefix_name + cobra_metabolite.name, 
                                      lower_bound=lower_bound, 
                                      upper_bound=upper_bound)
            drain_reaction.add_metabolites(object_stoichiometry)
            #  exchange reaction - ... provide matter influx or efflux to a model, for example to replenish a 
            #metabolic network with raw materials ... 
            drain_reaction.annotation[self.SBO_ANNOTATION] = sbo
            
            return drain_reaction
        
    def build(self, model_id = None):
        if model_id is None:
            model_id = self.fbamodel.id
            
        self.metabolites = {}
        self.reactions = {}
        self.biomass_reactions = set()
        
        self.sink_compounds = set()
        self.demand_compounds = set()
        self.exchange_compounds = set()
        
        for modelcompound in self.fbamodel.metabolites:
            cobra_metabolite = self.convert_modelcompound(modelcompound)
            
            if cobra_metabolite.id not in self.metabolites:
                self.metabolites[cobra_metabolite.id] = cobra_metabolite
                self.metabolites_remap[modelcompound.id] = cobra_metabolite.id
            else:
                logger.warning('duplicate compound: %s', cobra_metabolite.id)
                
            if cobra_metabolite.id in self.auto_sink:
                logger.info('Add Sink: [%s]', cobra_metabolite.id)
                self.demand_compounds.add(cobra_metabolite.id)
            if cobra_metabolite.compartment == self.auto_exchange:
                logger.debug('Add Exchange: [%s]', cobra_metabolite.id)
                self.exchange_compounds.add(cobra_metabolite.id)
                
        for modelreaction in self.fbamodel.reactions:
            cobra_reaction = self.convert_modelreaction(modelreaction)
            self.add_reaction(cobra_reaction)
                
        for biomass in self.fbamodel.data['biomasses']:
            cobra_reaction = self.convert_biomass_to_reaction(biomass)
            if not self.add_reaction(cobra_reaction) == None:
                self.biomass_reactions.add(cobra_reaction.id)
                
        for cpd_id in self.exchange_compounds:
            lower_bound = self.COBRA_DEFAULT_LB if len(self.media_const) == 0 else self.COBRA_0_BOUND
            upper_bound = self.COBRA_DEFAULT_UB
            if cpd_id in self.media_const:
                lower_bound, upper_bound = self.media_const[cpd_id]
            drain_reaction = self.build_drain_from_metabolite_id(cpd_id, lower_bound, upper_bound)
            self.add_reaction(drain_reaction)
            logger.debug('created exchange for [%s]: %s', cpd_id, drain_reaction)
        for cpd_id in self.demand_compounds:
            drain_reaction = self.build_drain_from_metabolite_id(cpd_id, self.COBRA_0_BOUND, self.COBRA_DEFAULT_UB, 
                                                                 "DM_", "Demand for ")
            self.add_reaction(drain_reaction)
            logger.debug('created demand for [%s]: %s', cpd_id, drain_reaction)
        for cpd_id in self.sink_compounds:
            drain_reaction = self.build_drain_from_metabolite_id(cpd_id, self.COBRA_0_BOUND, self.COBRA_DEFAULT_UB, 
                                                                 "SK_", "Sink for ")
            self.add_reaction(drain_reaction)
            logger.debug('created sink for [%s]: %s', cpd_id, drain_reaction)
        #print(self.genes)
        cobra_model = Model(model_id)
        for g in self.genes:
            gene = Gene(id=build_gene_id(g), name=g)
            gene.annotation[self.SBO_ANNOTATION] = "SBO:0000243"
            if g in self.gene_annotation:
                gene.annotation.update(self.gene_annotation[g])
            cobra_model.genes.append(gene)
        cobra_model.add_metabolites(list(self.metabolites.values()))
        cobra_model.add_reactions(list(self.reactions.values()))
        
        if len(self.biomass_reactions) > 0:
            default_biomass = list(self.biomass_reactions)[0]
            logger.info('Default biomass: [%s]', default_biomass)
            cobra_model.objective = default_biomass
            linear_reaction_coefficients(cobra_model)
            
        return cobra_model