import re
from cobrakbase.core.kbaseobject import KBaseObjectBase
from cobrakbase.core.utils import get_id_from_ref
from cobrakbase.core.kbasegenomes_feature import KBaseGenomeFeature


def normalize_role(s):
    #print(s)
    s = s.strip().lower()
    s = re.sub('[\W_]+', '', s) 
    return s


class KBaseGenome(KBaseObjectBase):
    
    @property
    def features(self):
        return list(map(lambda x: KBaseGenomeFeature(x), self.data['features']))
    
    def read_genome_aliases(self):
        gene_aliases = {}
        for feature in self.data['features']:
            gene_aliases[feature['id']] = {}
            if 'aliases' in feature and type(feature['aliases']) == list:
                for alias in feature['aliases']:
                    if type(alias) == list:
                        for a in alias:
                            #risk parsing the first element
                            self.get_old_alias(a, feature, gene_aliases)
                    else:
                        self.get_old_alias(alias, feature, gene_aliases)
                        #print('discard', alias)
            #print(feature['aliases' in ])
            db_refs = self.get_db_xrefs(feature)
            gene_aliases[feature['id']].update(db_refs)
        return gene_aliases
    
    def get_db_xrefs(self, feature):
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
    
    def get_old_alias(self, alias, feature, gene_aliases):
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
            
    def get_annotation(self):
        annotation = {}
        for f in self.data['features']:
            gene_id = f['id']
            #print(f)
            if 'functions' in f:
                annotation[gene_id] = set(f['functions'])
            elif 'function' in f:
                annotation[gene_id] = set([f['function']])
            else:
                annotation[gene_id] = set([None])
        return annotation
    
    def get_annotation2f(self, f):
        annotation = set([None])
        if 'functions' in f:
            annotation = set(f['functions'])
        elif 'function' in f:
            annotation = set([f['function']])
        return annotation

    def to_faa(self):
        faa_features = []

        for feature in self.data['features']:
            faa_features.append('>' + feature['id'] + '\n' + feature['protein_translation'])

        return '\n'.join(faa_features)
    
    def ontology_terms_to_reactions(self,reaction_ontology_hash,selected_events = {},select_all = 1):
        #If the genome has no ontology then we just exit
        if "ontology_events" not in self.data:
            return {} 
        #Creating events array - note I don't care if scores are normalized because reactions scores will be normalized
        event_array = []
        for event in self.data['ontology_events']:
            if "description" in event and event["description"] in selected_events:
                event_array.append(selected_events[event["description"]])
            elif event["id"]+"-"+event["method"]+"-"+event["timestamp"] in selected_events:
                event_array.append(selected_events[event["id"]+"-"+event["method"]+"-"+event["timestamp"]])
            elif select_all == 1:
                event_array.append(1)
            else:
                event_array.append(0)
        #Cycling through features and computing reaction-gene scores
        reaction_scores = {}
        count = 0
        average = 0
        stddev = 0
        for feature in self.data['features']:
            #Gene reaction scores are stored here then consolidated in the reaction_scores datastructure
            gene_reaction_scores = {}
            if "ontology_terms" in feature:
                for ontology in feature["ontology_terms"]:
                    for term in feature["ontology_terms"][ontology]:
                        if term in reaction_ontology_hash:
                            for reaction in reaction_ontology_hash[term]:
                                #Initializing reaction score
                                if reaction not in gene_reaction_scores:
                                    gene_reaction_scores[reaction] = 0
                                for event in feature["ontology_terms"][type][term]:
                                    if event_array[event] != 0:
                                        gene_reaction_scores[reaction] += event_array[event]
            #Consolidating gene-level scores into reaction_scores datastructure
            for reaction in gene_reaction_scores:
                if reaction not in reaction_scores:
                    reaction_scores[reaction] = {}
                reaction_scores[reaction][feature['id']] = gene_reaction_scores[reaction]
                average += gene_reaction_scores[reaction]
                count += 1
        average = average/count
        #Computing stddev of scores
        for reaction in reaction_scores:
            for gene in reaction_scores[reaction]:
                stddev += (reaction_scores[reaction][gene]-average)**2
        stddev = (stddev/count)**0.5
        #Normalizing scores        
        for reaction in reaction_scores:
            for gene in reaction_scores[reaction]:
                reaction_scores[reaction][gene] = reaction_scores[reaction][gene]/stddev
                if reaction_scores[reaction][gene] > 1:
                    reaction_scores[reaction][gene] = 1
        return reaction_scores