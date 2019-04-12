import pandas as pd

def get_low(ids):
    low = None
    ret = None
    for id in ids:
        if low == None or int(id[3:]) < low:
            low = int(id[3:])
            ret = id
    return ret

def make_alias_dict(compound_aliases):
    compound_alias = {}
    for row_id, d in compound_aliases.iterrows():
        #print(row_id, d)
        alias = d['External ID']
        seed_id = d['ModelSEED ID']
        #print()
        if not alias in compound_alias:
            compound_alias[alias] = {'seed_id' : seed_id}
    return compound_alias

def get_lhs_rhs(seed_reaction, eval_func):
    result = {}
    result_no_zero = {}
    stoichiometry = seed_reaction['stoichiometry']
    if type(stoichiometry) == str:
        for reagent_str in stoichiometry.split(';'):
            reagent_data = reagent_str.split(':')
            cpd_id = reagent_data[1]
            value = float(reagent_data[0])
            if eval_func(value):
                if not cpd_id in result:
                    result[cpd_id] = 0
                result[reagent_data[1]] += value
            elif value == 0:
                raise Exception('zero value stoich: ' + stoichiometry)
        
    for cpd_id in result:
        if result[cpd_id] == 0:
            print(f'{seed_reaction["id"]} contains compound bein transported {cpd_id}')
        else:
            result_no_zero[cpd_id] = result[cpd_id]
    return result_no_zero

def get_stoichiometry(seed_reaction):
    result = {}
    result_no_zero = {}
    stoichiometry = seed_reaction['stoichiometry']
    if type(stoichiometry) == str:
        for reagent_str in stoichiometry.split(';'):
            reagent_data = reagent_str.split(':')
            cpd_id = reagent_data[1]
            if not cpd_id in result:
                result[cpd_id] = 0
            result[reagent_data[1]] += float(reagent_data[0])
        
    for cpd_id in result:
        if result[cpd_id] == 0:
            print(f'{seed_reaction["id"]} contains compound bein transported {cpd_id}')
        else:
            result_no_zero[cpd_id] = result[cpd_id]
    return result_no_zero
                  
def get_cstoichiometry(seed_reaction):
    result = {}
    result_no_zero = {}
    stoichiometry = seed_reaction['stoichiometry']
    #print(stoichiometry)
    if type(stoichiometry) == str:
        for reagent_str in stoichiometry.split(';'):
            reagent_data = reagent_str.split(':')
            value = reagent_data[0]
            cpd_id = reagent_data[1]
            cmp_index = reagent_data[2]
            if not (cpd_id, cmp_index) in result:
                result[(cpd_id, cmp_index)] = 0
            result[(cpd_id, cmp_index)] += float(value)
        
    for p in result:
        if result[p] == 0:
            print(f'{seed_reaction["id"]} contains compound bein transported {p}')
        else:
            result_no_zero[p] = result[p]
    return result_no_zero

class ModelSEEDCompound:
    
    def __init__(self, data, api=None):
        self.data = data
        self.api = api
        
    @property
    def id(self):
        return self.data['id']
    
    @property
    def formula(self):
        return self.data['formula']
                  
    @property
    def database(self):
        return "seed.compound"

    @property
    def inchi(self):
        if not self.api == None:
            if self.id in self.api.compound_structures and 'InChI' in self.api.compound_structures[self.id]:
                  return self.api.compound_structures[self.id]['InChI']
        return None
                  
    @property
    def inchikey(self):
        if not self.api == None:
            if self.id in self.api.compound_structures and 'InChIKey' in self.api.compound_structures[self.id]:
                  return self.api.compound_structures[self.id]['InChIKey']
        if pd.isna(self.data['inchikey']):
            return None
        return self.data['inchikey']
                  
    @property
    def smiles(self):
        if not self.api == None:
            if self.id in self.api.compound_structures and 'SMILE' in self.api.compound_structures[self.id]:
                  return self.api.compound_structures[self.id]['SMILE']
        if pd.isna(self.data['smiles']):
            return None
        return self.data['smiles']
                  
    @property
    def aliases(self):
        if not self.api == None:
            if self.id in self.api.compound_aliases:
                  return self.api.compound_aliases[self.id]
        return {}
    
    @property
    def deltag(self):
        return self.data['deltag']
    
    @property
    def is_obsolete(self):
        if 'is_obsolete' in self.data:
            is_obsolete = self.data['is_obsolete']
            if is_obsolete == 0:
                return False
            else:
                return True
        return False
                  
class ModelSEEDReaction:
    
    def __init__(self, data, api=None):
        self.data = data
        self.api = api
        self.compounds = {}
        
    @property
    def id(self):
        return self.data['id']
    
    @property
    def stoichiometry(self):
        return get_stoichiometry(self.data)
                  
    @property
    def cstoichiometry(self):
        return get_cstoichiometry(self.data)

    @property
    def ec_numbers(self):
        if not self.api == None:
            if self.id in self.api.reaction_ecs:
                  return self.api.reaction_ecs[self.id]
        return {}
                  
    @property
    def database(self):
        return "seed.reaction"
                  
    @property
    def lhs(self):
        return get_lhs_rhs(self.data, lambda x : x < 0)
                  
    @property
    def rhs(self):
        return get_lhs_rhs(self.data, lambda x : x > 0)
    
    @property
    def is_transport(self):
        if 'is_transport' in self.data:
            is_transport = self.data['is_transport']
            if is_transport == 1:
                return True
                  
        if not len(self.lhs.keys() & self.rhs.keys()) == 0:
            return True
                  
        return False
                  
    @property
    def aliases(self):
        if not self.api == None:
            if self.id in self.api.reaction_aliases:
                  return self.api.reaction_aliases[self.id]
        return {}
    
    @property
    def is_obsolete(self):
        if 'is_obsolete' in self.data:
            is_obsolete = self.data['is_obsolete']
            if is_obsolete == 0:
                return False
            else:
                return True
        return False

class ModelSEED:
    
    def __init__(self, compounds, reactions, 
                 compound_aliases = {},
                 reaction_aliases = {},
                 compound_structures = {},
                 reaction_ecs = {}):
        self.compounds = compounds
        self.reactions = reactions
        self.compound_aliases = compound_aliases
        self.reaction_aliases = reaction_aliases
        self.compound_structures = compound_structures
        self.reaction_ecs = reaction_ecs
                  
    def summary(self):
        print("cpds:", len(self.compounds), "rxns:", len(self.reactions))
        print('structures', len(self.compound_structures))
        
    def get_formula(self, seed_id):
        return self.get_attribute('formula', seed_id)
    
    def get_name(self, seed_id):
        return self.get_attribute('name', seed_id)

    def get_attribute(self, attr, seed_id):
        seed = self.get_seed_compound(seed_id)
        if seed == None:
            return None
        if attr in seed:
            value = seed[attr]
            if not value == 'null':
                return seed[attr]
        return None
    
    def get_non_obsolete(self, seed_reaction):
        if not seed_reaction['is_obsolete'] == 0 and 'linked_reaction' in seed_reaction:
            for id in seed_reaction['linked_reaction'].split(';'):
                other = self.get_seed_reaction(id)
                if not other == None:
                    if other['is_obsolete'] == 0:
                        return other['id']

        return seed_reaction['id']

    def is_obsolete(self, seed_id):
        seed = self.get_seed_compound(seed_id)
        if seed == None:
            return None
        
        if 'is_obsolete' in seed:
            is_obsolete = seed['is_obsolete']
            if is_obsolete == 0:
                return False
            else:
                return True
        return None

    def get_seed_compound(self, seed_id):
        if seed_id in self.compounds:
            return ModelSEEDCompound(self.compounds[seed_id], self)
        return None
    
    def get_seed_reaction(self, seed_id):
        if seed_id in self.reactions:
            return ModelSEEDReaction(self.reactions[seed_id], self)
        return None

    def is_abstract(self, seed_id):
        return None
    
    def get_seed_compound_by_alias(self, database, cpd_id):
        o = None
        for o_id in self.compounds:
            aliases_str = self.compounds[o_id]['aliases']
            alias = dict((a.split(':')[0], a.split(':')[1]) for a in aliases_str.split(';'))
            if database in alias and cpd_id in alias[database].split('|'):
                o = self.compounds[o_id]
                break
        return o
    
    def get_seed_reaction_by_alias(self, id):
        o = None
        for o_id in self.reactions:
            if id in self.reactions[o_id]['aliases']:
                o = self.reactions[o_id]
                break
        return o

def get_aliases_from_df(df):
    aliases = {}
    for t in df.itertuples():
        seed_id = t[1]
        database_id = t[2]
        database = t[3]
        if not seed_id in aliases:
            aliases[seed_id] = {}
        if not database in aliases[seed_id]:
            aliases[seed_id][database] = set()
        aliases[seed_id][database].add(database_id)
    return aliases
    
def from_github(commit):
    print(commit)
    #https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/566a42f8c04a0dab4536b59377074ad23bcc08be/Biochemistry/reactions.tsv
    database_repo = 'https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase'
    reactions_url = database_repo + '/%s/Biochemistry/reactions.tsv' % commit
    compounds_url = database_repo + '/%s/Biochemistry/compounds.tsv' % commit
    reactions_aliases_url = database_repo + '/%s/Biochemistry/Aliases/Unique_ModelSEED_Reaction_Aliases.txt' % commit
    compounds_aliases_url = database_repo + '/%s/Biochemistry/Aliases/Unique_ModelSEED_Compound_Aliases.txt' % commit
    compounds_structures_url = database_repo + '/%s/Biochemistry/Structures/Unique_ModelSEED_Structures.txt' % commit
    reactions_ec_url = database_repo + '/%s/Biochemistry/Aliases/Unique_ModelSEED_Reaction_ECs.txt' % commit
    compounds = {}
    reactions = {}

    print('load:', reactions_url)
    seed_reactions = pd.read_csv(reactions_url, sep='\t', low_memory=False)
    
    for row_id, d in seed_reactions.iterrows():
        seed_reaction = build_reaction(d)
        reactions[seed_reaction['id']] = seed_reaction
        
    print('load:', compounds_url)
    seed_compounds = pd.read_csv(compounds_url, sep='\t', low_memory=False) #Columns (10,14,15) have mixed types.
    
    for row_id, d in seed_compounds.iterrows():
        seed_compound = build_compound(d)
        compounds[seed_compound['id']] = seed_compound
        
        
    compound_aliases = pd.read_csv(compounds_aliases_url, sep='\t')
    reaction_aliases = pd.read_csv(reactions_aliases_url, sep='\t')
    
    alias_to_database_to_cpd = get_aliases_from_df(compound_aliases)
    alias_to_database_to_rxn = get_aliases_from_df(reaction_aliases)
    print('load:', reactions_ec_url)
    df_reaction_ecs = pd.read_csv(reactions_ec_url, sep='\t')
    print('load:', compounds_structures_url)
    df_structures = pd.read_csv(compounds_structures_url, sep='\t')

    compound_structures = get_structures(df_structures)
    reaction_ecs = get_aliases_from_df(df_reaction_ecs)
    
    modelseed = ModelSEED(compounds, reactions, alias_to_database_to_cpd, alias_to_database_to_rxn, compound_structures, reaction_ecs)
    return modelseed

def from_local(path):
    database_repo = path
    reactions_url = database_repo + '/Biochemistry/reactions.tsv'
    compounds_url = database_repo + '/Biochemistry/compounds.tsv'
    reactions_aliases_url = database_repo + '/Biochemistry/Aliases/Unique_ModelSEED_Reaction_Aliases.txt' 
    compounds_aliases_url = database_repo + '/Biochemistry/Aliases/Unique_ModelSEED_Compound_Aliases.txt' 
    reactions_names_url = database_repo + '/Biochemistry/Aliases/Unique_ModelSEED_Reaction_Names.txt'
    compounds_names_url = database_repo + '/Biochemistry/Aliases/Unique_ModelSEED_Compound_Names.txt'
    compounds_structures_url = database_repo + '/Biochemistry/Structures/Unique_ModelSEED_Structures.txt'
    reactions_ec_url = database_repo + '/Biochemistry/Aliases/Unique_ModelSEED_Reaction_ECs.txt'
    
    compounds = {}
    reactions = {}
    
    print('load:', reactions_url)
    seed_reactions = pd.read_csv(reactions_url, sep='\t', low_memory=False)
    print('load:', compounds_url)
    seed_compounds = pd.read_csv(compounds_url, sep='\t', low_memory=False) #Columns (10,14,15) have mixed types.
    
    for row_id, d in seed_reactions.iterrows():
        seed_reaction = build_reaction(d)
        reactions[seed_reaction['id']] = seed_reaction

    for row_id, d in seed_compounds.iterrows():
        seed_compound = build_compound(d)
        compounds[seed_compound['id']] = seed_compound
        
    print('load:', compounds_structures_url)
    df_structures = pd.read_csv(compounds_structures_url, sep='\t')
    compound_structures = get_structures(df_structures)

    print('load:', compounds_aliases_url)
    df_compound_aliases = pd.read_csv(compounds_aliases_url, sep='\t')
    print('load:', reactions_aliases_url)
    df_reaction_aliases = pd.read_csv(reactions_aliases_url, sep='\t')
    print('load:', reactions_ec_url)
    df_reaction_ecs = pd.read_csv(reactions_ec_url, sep='\t')
    
    compound_aliases = get_aliases_from_df(df_compound_aliases)
    reaction_aliases = get_aliases_from_df(df_reaction_aliases)
    reaction_ecs = get_aliases_from_df(df_reaction_ecs)
    
    modelseed = ModelSEED(compounds, reactions, compound_aliases, reaction_aliases, compound_structures, reaction_ecs)
    
    return modelseed

def get_structures(seed_structures):
    compound_structures = {}
    
    for row_id, d in seed_structures.iterrows():
        seed_id = d['ID']
        t = d['Type']
        value = d['Structure']
        if not seed_id in compound_structures:
            compound_structures[seed_id] = {}
        if t in compound_structures[seed_id]:
            print('warning duplicate structure:', t, seed_id)
        compound_structures[seed_id][t] = value
    
    return compound_structures
                  
def build_compound(d):
    seed_compound = {
        'id': d['id'],
        'abbreviation': d['abbreviation'],
        'name': d['name'],
        'formula': d['formula'],
        'mass': d['mass'],
        'source': d['source'],
        'inchikey': d['inchikey'],
        'charge': d['charge'],
        'is_core': d['is_core'],
        'is_obsolete': d['is_obsolete'],
        'linked_compound': d['linked_compound'],
        'is_cofactor': d['is_cofactor'],
        'deltag': d['deltag'],
        'deltagerr': d['deltagerr'],
        'pka': d['pka'],
        'pkb': d['pkb'],
        'abstract_compound': d['abstract_compound'],
        'comprised_of': d['comprised_of'],
        'aliases': d['aliases'],
        'smiles': d['smiles']
    }
    return seed_compound

def build_reaction(d):
    seed_reaction = {
            'id': d['id'],
            'abbreviation': d['abbreviation'],
            'name': d['name'],
            'code': d['code'],
            'stoichiometry': d['stoichiometry'],
            'is_transport': d['is_transport'],
            'equation': d['equation'],
            'definition': d['definition'],
            'reversibility': d['reversibility'],
            'direction': d['direction'],
            'abstract_reaction': d['abstract_reaction'],
            'pathways': d['pathways'],
            'aliases': d['aliases'],
            'ec_numbers': d['ec_numbers'],
            'deltag': d['deltag'],
            'deltagerr': d['deltagerr'],
            'compound_ids': d['compound_ids'],
            'status': d['status'],
            'is_obsolete': d['is_obsolete'],
            'linked_reaction': d['linked_reaction'],
            'notes': d['notes'],
            'source': d['source']
    }
    return seed_reaction