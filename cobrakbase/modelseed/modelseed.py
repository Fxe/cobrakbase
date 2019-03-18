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

def get_stoichiometry(seed_reaction):
    result = {}
    stoichiometry = seed_reaction['stoichiometry']
    for reagent_str in stoichiometry.split(';'):
        reagent_data = reagent_str.split(':')
        if not reagent_data[1] in result:
            result[reagent_data[1]] = 0
        else:
            print('duplicate', reagent_data, stoichiometry)
        result[reagent_data[1]] = float(reagent_data[0])
    return result

class ModelSEEDReaction:
    
    def __init__(self, data):
        self.data = data
        
    @property
    def id(self):
        return self.data['id']
    
    @property
    def stoichiometry(self):
        result = {}
        stoichiometry = self.data['stoichiometry']
        for reagent_str in stoichiometry.split(';'):
            reagent_data = reagent_str.split(':')
            if not reagent_data[1] in result:
                result[reagent_data[1]] = 0
            else:
                print('duplicate', reagent_data, stoichiometry)
            result[reagent_data[1]] = float(reagent_data[0])
        return result
    
    @property
    def is_transport(self):
        if 'is_transport' in self.data:
            is_transport = self.data['is_transport']
            if is_transport == 0:
                return False
            else:
                return True
        return False
    
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
    
    def __init__(self, compounds, reactions, alias_to_database_to_cpd = {}, alias_to_database_to_rxn = {}):
        self.compounds = compounds
        self.reactions = reactions
        self.alias_to_database_to_cpd = alias_to_database_to_cpd
        self.alias_to_database_to_rxn = alias_to_database_to_rxn
        print("cpds:", len(self.compounds), "rxns:", len(self.reactions))
        
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
            return self.compounds[seed_id]
        return None
    
    def get_seed_reaction(self, seed_id):
        if seed_id in self.reactions:
            return self.reactions[seed_id]
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
    
    
def from_github(commit):
    print(commit)
    #https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/566a42f8c04a0dab4536b59377074ad23bcc08be/Biochemistry/reactions.tsv
    database_repo = 'https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase'
    reactions_url = database_repo + '/%s/Biochemistry/reactions.tsv' % commit
    compounds_url = database_repo + '/%s/Biochemistry/compounds.tsv' % commit
    reactions_aliases_url = database_repo + '/%s/Biochemistry/Aliases/Unique_ModelSEED_Reaction_Aliases.txt' % commit
    compounds_aliases_url = database_repo + '/%s/Biochemistry/Aliases/Unique_ModelSEED_Compound_Aliases.txt' % commit
    
    compounds = {}
    reactions = {}

    print('load:', reactions_url)
    seed_reactions = pd.read_csv(reactions_url, sep='\t')
    
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
    
    alias_to_database_to_cpd = make_alias_dict(compound_aliases)
    alias_to_database_to_rxn = make_alias_dict(reaction_aliases)
    
    modelseed = ModelSEED(compounds, reactions, alias_to_database_to_cpd, alias_to_database_to_rxn)
    return modelseed

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