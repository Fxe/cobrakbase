import math
from cobra.core.gene import parse_gpr, ast2str

def get_compound_references(model):
    compounds_to_refs = {}
    for m in model.metabolites:
        if not m.id in compounds_to_refs:
            compounds_to_refs[m.id] = '~/modelcompounds/id/' + m.id
    return compounds_to_refs

def convert_to_kbase(id, model):
    modelcompartments = []
    biomasses = []
    modelcompounds = []
    modelreactions = []
    
    compounds_to_refs = get_compound_references(model)
    compartments_to_refs = {
        'c' : '~/modelcompartments/id/c0',
        'e' : '~/modelcompartments/id/e0',
    }
    
    for m in model.metabolites:
        compound_ref = '~/template/compounds/id/cpd00000'
        formula = '*'
        if not m.formula == None:
            formula = m.formula
        if m.id.startswith('cpd'):
            compound_ref = '~/template/compounds/id/' + m.id.split('_')[0].strip()
            
        modelcompartment_ref = '~/modelcompartments/id/c0'
        
        if m.compartment in compartments_to_refs:
            modelcompartment_ref = compartments_to_refs[m.compartment]
        else:
            print('undeclared compartment:', m.compartment)
            
        modelcompound = {
            'aliases': [], 
            'charge': m.charge, 
            'compound_ref': compound_ref, 
            'dblinks': {}, 
            'formula': formula, 
            'id': m.id, 
            'modelcompartment_ref': modelcompartment_ref, 
            'name': m.name, 
            'numerical_attributes': {}, 
            'string_attributes': {}
        }
        modelcompounds.append(modelcompound)
        
    for r in model.reactions:
        modelreaction = convert_to_kbase_reaction(r, compounds_to_refs)
        if not modelreaction == None:
            modelreactions.append(modelreaction)
    #'biomasses', 'delete_biomasses', 'deleted_reactions', 'gapfilledcandidates', 'gapfillings', 'gapgens', 'genome_ref', 'id', 'model_edits', 'modelcompartments', 'modelcompounds', 'modelreactions', 'name', 'quantopts', 'source', 'source_id', 'template_ref', 'template_refs', 'type'
    kmodel = {
        'gapfilledcandidates' : [],
        'gapgens' : [],
        'gapfillings' : [],
        'id' : id,
        'genome_ref' : "38412/14/1",   #genome_ref
        'template_ref' : "12998/1/2", #template
        'template_refs' : ["12998/1/2"],
        'name' : model.name,
        'type' : "GenomeScale",
        'source' : 'cobrapy',
        'source_id' : model.id,
        'biomasses' : biomasses,
        'modelcompartments' : modelcompartments,
        'modelcompounds' : modelcompounds,
        'modelreactions' : modelreactions,
    }
    return kmodel

#print(r.lower_bound, r.upper_bound)
def get_bounds(reaction):
    maxrevflux = math.fabs(reaction.lower_bound)
    maxforflux = math.fabs(reaction.upper_bound)
    direction = '='
    if maxrevflux == 0 and maxforflux > 0:
        direction = '>'
    elif maxrevflux > 0 and maxforflux == 0:
        direction = '<'
        
    return maxrevflux, maxforflux, direction


def build_model_reaction_proteins(cobra_gpr_str):
    #DUMB VERSION
    ast = parse_gpr(cobra_gpr_str)
    #print(ast)
    #print(len(ast))
    #print(ast[0].body)
    proteins = []
    for a in set(ast[1]):
        proteins.append([a])
    return proteins

#'modelReactionProteins': [{'complex_ref': '~/template/complexes/name/cpx00700',
#   'modelReactionProteinSubunits': [{'feature_refs': ['~/genome/features/id/b3177'],
#     'note': '',
#     'optionalSubunit': 0,
#     'role': 'Dihydropteroate synthase (EC 2.5.1.15)',
#     'triggering': 1}],
#   'note': '',
#   'source': ''}],
def build_model_reaction_proteins2(gene_sets):
    model_reaction_proteins = []
    for gs in gene_sets:
        model_reaction_protein_subunits = []
        for g in gs:
            subunit = {
                'feature_refs': ['~/genome/features/id/' + g],
                'note': '',
                'optionalSubunit': 0,
                'role': '',
                'triggering': 1
            }
            model_reaction_protein_subunits.append(subunit)
            
        model_reaction_protein = {
            'complex_ref' : '~/template/complexes/name/cpx00000',
            'note': '',
            'source': '',
            'modelReactionProteinSubunits' : model_reaction_protein_subunits
        }
        model_reaction_proteins.append(model_reaction_protein)
    return model_reaction_proteins

def convert_to_kbase_reaction(reaction, compounds_to_refs):
    modelReactionReagents = []
    for o in reaction.metabolites:
        if o.id in compounds_to_refs:
            modelReactionReagent = {
                'coefficient': reaction.metabolites[o], 
                'modelcompound_ref': compounds_to_refs[o.id]
            }
            modelReactionReagents.append(modelReactionReagent)
        else:
            print('discarded undeclared compound:', o.id)
        #print(o, reaction.metabolites[o])
        
    maxrevflux, maxforflux, direction = get_bounds(reaction)
    
    model_reaction_proteins = []
    if len(reaction.gene_reaction_rule) > 0:
        gpr = reaction.gene_reaction_rule
        model_reaction_proteins = build_model_reaction_proteins2(build_model_reaction_proteins(gpr))
    
    modelreaction = {
        'aliases': [], 
        'dblinks': {}, 
        'direction': direction, 
        'edits': {}, 
        'gapfill_data': {}, 
        'id': reaction.id, 
        'maxforflux': maxforflux, 
        'maxrevflux': maxrevflux, 
        'modelReactionProteins': model_reaction_proteins, 
        'modelReactionReagents': modelReactionReagents, 
        'modelcompartment_ref': '~/modelcompartments/id/c0', 
        'name': reaction.name, 
        'numerical_attributes': {}, 
        'probability': 0, 
        'protons': 0, 
        'reaction_ref': '~/template/reactions/id/' + reaction.id, 
        'string_attributes': {}
    }
    return modelreaction