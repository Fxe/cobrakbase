import logging
import os
import json
import cobra
from cobrakbase.core.utils import get_str, get_int, get_id_from_ref
from cobrakbase.core.converters import KBaseFBAModelToCobraBuilder
from cobrakbase.kbaseapi import KBaseAPI
from cobrakbase.Workspace.WorkspaceClient import Workspace as WorkspaceClient
from cobra.core import Gene, Metabolite, Model, Reaction
from cobra.util.solver import linear_reaction_coefficients
import cobrakbase.core.model
import cobrakbase.core.converters
import cobrakbase.core.kbasefba
import cobrakbase.modelseed.utils
import cobrakbase.modelseed.stoich_integration
import cobrakbase.modelseed.hierarchical_ontology
import cobrakbase.modelseed.modelseed

__author__  = "Filipe Liu"
__email__   = "fliu@anl.gov"
__version__ = "0.2.7"

print("cobrakbase", __version__)

KBASE_WS_URL = "https://kbase.us/services/ws/"
DEV_KBASE_WS_URL = "https://appdev.kbase.us/services/ws/"

SBO_ANNOTATION = "sbo"

bigg = False

API = None

logging.basicConfig()
logger = logging.getLogger(__name__)

def read_model(id, workspace):
    if API == None:
        print("Login first! cobrakbase.login(<API_TOKEN>)")
        return None
    data = API.get_object(id, workspace)
    return convert_kmodel(data)

def read_model_with_media(modelId, mediaId, workspace):
    if API == None:
        print("Login first! cobrakbase.login(<API_TOKEN>)")
        return None
    model_data = API.get_object(modelId, workspace)
    media_data = API.get_object(mediaId, workspace)
    media = convert_media(media_data)
    #print(media)
    return convert_kmodel(model_data, media)

def login(token, dev=False):
    global API
    API = KBaseAPI(token, dev)

SINK = ["cpd02701_c0", "cpd11416_c0", "cpd15302_c0", "cpd11416_c0"]

COBRA_DEFAULT_LB = -1000000
COBRA_DEFAULT_UB =  1000000
COBRA_0_BOUND = 0

def convert_biomass_to_reaction(biomass, mets):
    mr_id = biomass['id'] + "_biomass"
    name = biomass['name']
    object_stoichiometry = {}
    for biomasscompound in biomass['biomasscompounds']:
        coefficient = biomasscompound['coefficient']
        modelcompound_ref = biomasscompound['modelcompound_ref']
        mc_id = get_id_from_ref(modelcompound_ref)
        met_id = build_cpd_id(mc_id)
        met = mets[mc_id]
        object_stoichiometry[met] = coefficient
    reaction = Reaction(id=build_rxn_id(mr_id), name=name, lower_bound=COBRA_0_BOUND, upper_bound=COBRA_DEFAULT_UB)
    objective_id = reaction.id
    reaction.add_metabolites(object_stoichiometry)
    #SBO:0000629 [biomass production]
    #Biomass production, often represented 'R_BIOMASS_', is usually the optimization target reaction of constraint-based models ...
    reaction.annotation[SBO_ANNOTATION] = "SBO:0000629" 
    return reaction

def get_reaction_constraints(data):
    #clean this function !
    if 'maxrevflux' in data and 'maxforflux' in data:
        if data['maxrevflux'] == 1000000 and data['maxforflux'] == 1000000:
            if 'direction' in data:
                if data['direction'] == '>':
                    return 0, 1000
                elif data['direction'] == '<':
                    return -1000, 0
                else:
                    return -1000, 1000
            else:
                return -1 * data['maxrevflux'], data['maxforflux']
        else:
            return -1 * data['maxrevflux'], data['maxforflux']
    return -1000, 1000

def convert_kmodel(kmodel, media=None, exchanges = True, model_id = "kbase"):
    model_test = cobra.Model(model_id)

    comps = {}
    mets = {}
    sink = set()
    reactions = []
    extra = set()

    for mcomp in kmodel['modelcompartments']:
        mcomp_id = mcomp['id']
        name = mcomp['label']
        comps[mcomp_id] = name

    for mc in kmodel["modelcompounds"]:
        #print(mc.keys())
        formula = None
        if not mc['formula'] == 'null':
            formula = mc['formula']
        name = mc['name']
        charge = get_int('charge', 0, mc)
        mc_id = mc['id']
        annotation = {}
        if 'dblinks' in mc:
            annotation = get_cpd_annotation(mc['dblinks'])
        compartment = get_compartment_id(mc, simple=True)
        id = build_cpd_id(mc_id)
        if bigg:
            if "bigg.metabolite" in annotation:
                id = annotation["bigg.metabolite"] + "_" + compartment
                #print(id)
        
        if mc_id in SINK:
            logger.info('Add Sink: [%s]', mc_id)
            extra.add(mc_id)
            sink.add(mc_id)
        if compartment.startswith("e"):
            extra.add(mc_id)
            
        met = Metabolite(id=id, formula=formula, name=name, charge=charge, compartment=compartment)
        met.annotation[SBO_ANNOTATION] = "SBO:0000247" #simple chemical - Simple, non-repetitive chemical entity.
        if id.startswith('cpd'):
            met.annotation["seed.compound"] = id.split("_")[0]
        #met.annotation[""] = "!!!"
        met.annotation.update(annotation)
        mets[mc_id] = met

    genes = set()
        #print(mc)
    for mr in kmodel["modelreactions"]:
        mr_id = mr['id']
        name = mr['name']
        
        lower_bound, upper_bound = get_reaction_constraints(mr)
        annotation = {}
        if 'dblinks' in mr:
            annotation = get_rxn_annotation(mr['dblinks'])
        id = build_rxn_id(mr_id)
        if bigg:
            if "bigg.reaction" in annotation:
                id = annotation["bigg.reaction"]
        #print(id)
        reaction = Reaction(id=id, name=name, lower_bound=lower_bound, upper_bound=upper_bound)
        #print(mr['maxrevflux'], mr['maxforflux'], reaction.lower_bound)
        reaction.annotation[SBO_ANNOTATION] = "!!!"
        if id.startswith('rxn'):
            reaction.annotation["seed.reaction"] = id.split("_")[0]
        reaction.annotation.update(annotation)
        object_stoichiometry = {}
        for mrr in mr['modelReactionReagents']:
            modelcompound_ref = mrr['modelcompound_ref']
            coefficient = mrr['coefficient']
            mc_id = get_id_from_ref(modelcompound_ref)
            met_id = build_cpd_id(mc_id)
            met = mets[mc_id]#model_test.metabolites.get_by_id(met_id)
            #print(met, met_id, coefficient)
            object_stoichiometry[met] = coefficient
        reaction.annotation[SBO_ANNOTATION] = "SBO:0000176" #biochemical reaction
        reaction.add_metabolites(object_stoichiometry)
        gpr = get_gpr(mr)
        gpr_string = get_gpr_string(gpr)
        #print(gpr_string)
        reaction.gene_reaction_rule = gpr_string
        genes |= get_genes(gpr)
        #print(reaction)
        reactions.append(reaction)
        #print(mr.keys())

    objective_id = None
    for biomass in kmodel['biomasses']:
        reaction = convert_biomass_to_reaction(biomass, mets)
        reactions.append(reaction)
        objective_id = reaction.id
        #print(biomass)
    #print(media)
    
    if exchanges:
        logger.info('Setup Drains. EX: %d SK: %d', len(extra), len(sink))
        for e in extra:
            met = mets[e]
            prefix = "EX_"
            if e in sink:
                prefix = "DM_"
            id = prefix + met.id
            lower_bound = COBRA_DEFAULT_LB
            upper_bound = COBRA_DEFAULT_UB
            if not media == None:
                lower_bound = 0
            if not media == None and e.split("_")[0] in media:
                ct = media[e.split("_")[0]]
                lower_bound = ct[0]
                upper_bound = ct[1]

            #print(e, met, id, lower_bound, upper_bound)

            object_stoichiometry = {met : -1}
            reaction = Reaction(id=id, name="Exchange for " + met.name, lower_bound=lower_bound, upper_bound=upper_bound)
            reaction.add_metabolites(object_stoichiometry)
            reaction.annotation[SBO_ANNOTATION] = "SBO:0000627" #exchange reaction - ... provide matter influx or efflux to a model, for example to replenish a metabolic network with raw materials ... 
            reactions.append(reaction)
            #print(reaction.name)
    #print("Genes:", genes)
    for g in genes:
        gene = Gene(id=build_gene_id(g), name=g)
        gene.annotation[SBO_ANNOTATION] = "SBO:0000243"
        model_test.genes.append(gene)

    model_test.compartments = comps
    #model_test.add_metabolites(mets.values)
    try:
        model_test.add_reactions(reactions)
    except ValueError as e:
        warn(str(e))
    
    if not objective_id == None:
        model_test.objective = model_test.reactions.get_by_id(id=objective_id)
        linear_reaction_coefficients(model_test)
    return model_test


def read_kbase_model(filename):
    kmodel = {}
    with open(filename) as file:
        data = file.read()
        kmodel = json.loads(data)
    return kmodel

def read_json(filename, converter):
    di = None
    if os.path.exists(filename):
        with open(filename) as file:
            data = file.read()
            di = json.loads(data)
    if di is None:
        return None
    return converter(di)

def convert_media(kmedia):
    media = {}
    for mediacompound in kmedia['mediacompounds']:
        met_id = get_id_from_ref(mediacompound['compound_ref'])
        lb = -1 * mediacompound['maxFlux']
        ub = -1 * mediacompound['minFlux']
        media[met_id] = (lb, ub)
    return media

def read_kbase_media(filename):
    return read_json(filename, convert_media)

def get_compartment_id(modelcompound, simple=False):
    modelcompartment_ref = modelcompound['modelcompartment_ref']
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
    #print(dblinks)
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
    #if gpr_string.startswith("(") and gpr_string.endswith(")"):
    #    gpr_string = gpr_string[1:-1].strip()
    return gpr_string

def get_gpr(mr):
    gpr = []
    for mrp in mr['modelReactionProteins']:
        #print(mrp.keys())
        gpr_and = set()
        for mrps in mrp['modelReactionProteinSubunits']:
            #print(mrps.keys())
            for feature_ref in mrps['feature_refs']:
                gpr_and.add(get_id_from_ref(feature_ref))
        if len(gpr_and) > 0:
            gpr.append(gpr_and)
    return gpr



def read_modelseed_compound_aliases2(df):
    aliases = {}
    for a, row in df.iterrows():
        cpd_id = row[0]
        database_id = row[1]
        database = row[2]
        if not cpd_id in aliases:
            aliases[cpd_id] = {}
        
        if database == 'BiGG' or 'BiGG' in database:
            aliases[cpd_id]['bigg.metabolite'] = database_id
        if database == 'MetaCyc' or 'MetaCyc' in database:
            aliases[cpd_id]['biocyc'] = database_id
        if (database == 'KEGG' or 'KEGG' in database) and database_id[0] == 'C':
            aliases[cpd_id]['kegg.compound'] = database_id
    return aliases

def read_modelseed_reaction_aliases2(df):
    aliases = {}
    for a, row in df.iterrows():
        #print(row)
        #break
        rxn_id = row[0]
        database_id = row[1]
        database = row[2]
        if not rxn_id in aliases:
            aliases[rxn_id] = {}
        if database == 'BiGG' or 'BiGG' in database:
            aliases[rxn_id]['bigg.reaction'] = database_id
        if database == 'MetaCyc' or 'MetaCyc' in database:
            aliases[rxn_id]['biocyc'] = database_id
        if (database == 'KEGG' or 'KEGG' in database) and database_id[0] == 'R':
            aliases[rxn_id]['kegg.reaction'] = database_id
    return aliases

def read_modelseed_compound_aliases(df):
    aliases = {}
    for a, row in df.iterrows():
        if row[3] == 'BiGG':
            if not row[0] in aliases:
                aliases[row[0]] = {}
            aliases[row[0]]['bigg.metabolite'] = row[2]
        if row[3] == 'MetaCyc':
            if not row[0] in aliases:
                aliases[row[0]] = {}
            aliases[row[0]]['biocyc'] = row[2]
        if row[3] == 'KEGG' and row[2][0] == 'C':
            if not row[0] in aliases:
                aliases[row[0]] = {}
            aliases[row[0]]['kegg.compound'] = row[2]
    return aliases

def read_modelseed_reaction_aliases(df):
    aliases = {}
    for a, row in df.iterrows():
        if row[3] == 'BiGG':
            if not row[0] in aliases:
                aliases[row[0]] = {}
            aliases[row[0]]['bigg.reaction'] = row[2]
        if row[3] == 'MetaCyc':
            if not row[0] in aliases:
                aliases[row[0]] = {}
            aliases[row[0]]['biocyc'] = row[2]
        if row[3] == 'KEGG' and row[2][0] == 'R':
            if not row[0] in aliases:
                aliases[row[0]] = {}
            aliases[row[0]]['kegg.reaction'] = row[2]
    return aliases

def read_modelseed_compound_structures(df):
    structures = {}
    for _, row in df.iterrows():
        #print(row[0], row[1], row[3])
        if row[1] == 'InChIKey':
            if not row[0] in structures:
                structures[row[0]] = {}
            structures[row[0]]['inchikey'] = row[3]
    return structures

def get_old_alias(alias, feature, gene_aliases):
    if alias.startswith('EcoGene:'):
        gene_aliases[feature['id']]['ecogene'] = alias.split(':')[1]
    elif alias.startswith('UniProtKB/Swiss-Prot:'):
        gene_aliases[feature['id']]['uniprot'] = alias.split(':')[1]
    elif alias.startswith('NP_'):
        gene_aliases[feature['id']]['ncbiprotein'] = alias
    elif alias.startswith('ASAP:'):
        gene_aliases[feature['id']]['asap'] = alias.split(':')[1]
    elif alias.startswith('GI:'):
        gene_aliases[feature['id']]['ncbigi'] = alias
    elif alias.startswith('GeneID:'):
        gene_aliases[feature['id']]['ncbigene'] = alias.split(':')[1]
    else:
        1

def get_db_xrefs(feature):
    aliases = {}
    if 'db_xrefs' in feature:
        for ref in feature['db_xrefs']:
            db = ref[0]
            value = ref[1]
            if db == 'EcoGene':
                aliases['ecogene'] = value
            elif db == 'GeneID':
                aliases['ncbigene'] = value
    return aliases
        
def read_genome_aliases(genome):
    gene_aliases = {}
    for feature in genome['features']:
        gene_aliases[feature['id']] = {}
        if 'aliases' in feature and type(feature['aliases']) == list:
            for alias in feature['aliases']:
                if type(alias) == list:
                    for a in alias:
                        #risk parsing the first element
                        get_old_alias(a, feature, gene_aliases)
                else:
                    get_old_alias(alias, feature, gene_aliases)
                    #print('discard', alias)
        #print(feature['aliases' in ])
        db_refs = get_db_xrefs(feature)
        gene_aliases[feature['id']].update(db_refs)
    return gene_aliases

def is_transport(r):
    lhs = set()
    rhs = set()
    for m in r.reactants:
        if 'seed.compound' in m.annotation:
            lhs.add(m.annotation['seed.compound'])
        else:
            return False
    for m in r.products:
        if 'seed.compound' in m.annotation:
            rhs.add(m.annotation['seed.compound'])
        else:
            return False
    
    if not len(lhs & rhs) == 0:
        return True
    
    return False


def is_translocation(r):
    cmps = set()
    
    for m in r.reactants:
        cmps.add(m.compartment)
    for m in r.products:
        cmps.add(m.compartment)
    
    return len(cmps) > 1

def annotate_model_with_genome(model, genome):
    gene_aliases = cobrakbase.read_genome_aliases(genome)
    for g in model.genes:
        if g.id in gene_aliases:
            g.annotation.update(gene_aliases[g.id])

def annotate_model_metabolites_with_modelseed(model, modelseed):
    for m in model.metabolites:
        seed_id = None
        if 'seed.compound' in m.annotation:
            annotation = {}
            seed_id = m.annotation['seed.compound']
            seed_cpd = modelseed.get_seed_compound(seed_id)
            if not seed_cpd == None:
                if not seed_cpd.inchi == None:
                    annotation['inchi'] = seed_cpd.inchi
                if not seed_cpd.inchikey == None:
                    annotation['inchikey'] = seed_cpd.inchikey
                alias = seed_cpd.aliases
                if 'BiGG' in alias:
                    annotation['bigg.metabolite'] = list(alias['BiGG'])
                if 'KEGG' in alias:
                    annotation['kegg.compound'] = list(alias['KEGG'])
                if 'metanetx.chemical' in alias:
                    annotation['metanetx.chemical'] = list(alias['metanetx.chemical'])
                if 'MetaCyc' in alias:
                    annotation['biocyc'] = list(map(lambda x : 'META:' + x, alias['MetaCyc']))
            m.annotation.update(annotation)
            
def annotate_model_reactions_with_modelseed(model, modelseed):
    for r in model.reactions:
        seed_id = None
        if 'seed.reaction' in r.annotation:
            annotation = {}
            seed_id = r.annotation['seed.reaction']
            seed_rxn = modelseed.get_seed_reaction(seed_id)
            
            if not seed_rxn == None:
                alias = seed_rxn.aliases
                if 'BiGG' in alias:
                    annotation['bigg.reaction'] = list(alias['BiGG'])
                if 'KEGG' in alias:
                    annotation['kegg.reaction'] = list(alias['KEGG'])
                if 'rhea' in alias:
                    annotation['rhea'] = list(alias['rhea'])
                if 'metanetx.reaction' in alias:
                    annotation['metanetx.reaction'] = list(alias['metanetx.reaction'])
                if 'MetaCyc' in alias:
                    annotation['biocyc'] = list(map(lambda x : 'META:' + x, alias['MetaCyc']))
                ec_numbers = set()
                if 'Enzyme Class' in seed_rxn.ec_numbers:
                    for ec in seed_rxn.ec_numbers['Enzyme Class']:
                        if ec.startswith('EC-'):
                            ec_numbers.add(ec[3:])
                        else:
                            ec_numbers.add(ec)
                if len(ec_numbers) > 0:
                    annotation['ec-code'] = list(ec_numbers)
            r.annotation.update(annotation)
            
def annotate_model_with_modelseed(model, modelseed):
    annotate_model_metabolites_with_modelseed(model, modelseed)
    annotate_model_reactions_with_modelseed(model, modelseed)
            
    for r in model.reactions:
        if cobrakbase.is_translocation(r):
            if cobrakbase.is_transport(r):
                r.annotation['sbo'] = 'SBO:0000655'
            else:
                r.annotation['sbo'] = 'SBO:0000185'
                
    kbase_sinks = ['rxn13783_c0', 'rxn13784_c0', 'rxn13782_c0']
    
    for r in model.reactions:
        #r.annotation['ec-code'] = '1.1.1.1'
        #r.annotation['metanetx.reaction'] = 'MNXR103371'
        if r.id in kbase_sinks:
            r.annotation['sbo'] = 'SBO:0000632'
        if r.id.startswith('DM_'):
            r.annotation['sbo'] = 'SBO:0000628'
            
def detect_gapfilling_constrainst(kmodel, api):
    if 'gapfillings' in kmodel and len(kmodel['gapfillings']) > 0:
        print("Pulling media from gapfilling...", kmodel['gapfillings'])
        ref = api.get_object_info_from_ref(kmodel['gapfillings'][0]['media_ref'])
        o_data = api.get_object(ref.id, ref.workspace_id)
        return convert_media(o_data)
    return None