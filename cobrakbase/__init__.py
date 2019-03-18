import os
import json
import cobra
from cobrakbase.kbaseapi import KBaseAPI
from cobrakbase.Workspace.WorkspaceClient import Workspace as WorkspaceClient
from cobra.core import Gene, Metabolite, Model, Reaction
from cobra.util.solver import linear_reaction_coefficients
import cobrakbase.core.model
import cobrakbase.modelseed.utils
import cobrakbase.modelseed.modelseed

__author__  = "Filipe Liu"
__email__   = "fliu@anl.gov"
__version__ = "0.1.4"

print("cobrakbase", __version__)

KBASE_WS_URL = "https://kbase.us/services/ws/"
DEV_KBASE_WS_URL = "https://appdev.kbase.us/services/ws/"

SBO_ANNOTATION = "sbo"

bigg = False

API = None

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

def convert_kmodel(kmodel, media=None):
    model_test = cobra.Model("kbase")

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
        formula = mc['formula']
        name = mc['name']
        charge = mc['charge']
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
            print("Add Sink", mc_id)
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
        
        lower_bound = 0
        upper_bound = 0
        if 'maxrevflux' in mr:
            lower_bound = -1 * mr['maxrevflux']
        if 'maxforflux' in mr:
            upper_bound = mr['maxforflux']
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
    
    print("Setup Drains. EX:", len(extra), "SK:", len(sink))
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

def get_id_from_ref(str, stok='/'):
    return str.split(stok)[-1]

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