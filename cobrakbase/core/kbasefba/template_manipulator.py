import logging
from cobrakbase.core.kbasegenomesgenome import normalize_role

logger = logging.getLogger(__name__)

class TemplateManipulator:
    def __init__(self, template):
        self.template = template
    
    def get_role_to_rxn_ids(self):
        role_to_rxn_ids = {}
        for o in self.template.data['reactions']:
            trxn = self.template.get_reaction(o['id'])
            for role_id in trxn.get_roles():
                if not role_id in role_to_rxn_ids:
                    role_to_rxn_ids[role_id] = set()
                role_to_rxn_ids[role_id].add(trxn.id)
        
        return role_to_rxn_ids
    
    def get_search_name_to_role_id(self):
        # get duplicates
        search_name_to_role_id = {}
        for role in self.template.data['roles']:
            n = normalize_role(role['name'])
            if not n in search_name_to_role_id:
                search_name_to_role_id[n] = set()
            search_name_to_role_id[n].add(role['id'])
        return search_name_to_role_id
    
    def clear_orphan_roles(self):
        role_to_rxn_ids = self.get_role_to_rxn_ids()
        used_roles = set(role_to_rxn_ids)
        search_name_to_role_id = self.get_search_name_to_role_id()
    
        to_delete = set()
        to_update = set()
        for sn in search_name_to_role_id:
            role_ids = list(sorted(search_name_to_role_id[sn]))
            if len(search_name_to_role_id[sn]) > 1:
                selected = []
                for role_id in role_ids:
                    rxn_count = len(role_to_rxn_ids[role_id]) if role_id in role_to_rxn_ids else 0
                    if rxn_count > 0:
                        selected.append(role_id)
                if len(selected) == 0:
                    selected.append(role_ids[0])
                if len(selected) == 1:
                    s = selected[0]
                    role = self.template.get_role(s)
                    to_update.add(s)
                    for role_id in role_ids:
                        if not role_id == s:
                            to_delete.add(role_id)
                            other_role = self.template.get_role(role_id)
                            role['aliases'].append('alias:' + other_role['name'])
                else:
                    logger.warning('unable to select role %s', role_ids)

        self.template.data['roles']= list(filter(lambda x : x['id'] not in to_delete, self.template.data['roles']))
        
        return to_update, to_delete
    
    def clean_template(self, source_allow):
        search_name_to_role_id = self.get_search_name_to_role_id()

        # clear roles
        role_source = {}
        roles_to_clear = set()
        seed_roles = set()
        for o in self.template.data['roles']:
            role_source[o['id']] = o['source']
            if not o['source'] == source_allow:
                roles_to_clear.add(o['id'])
            else:
                seed_roles.add(o['id'])

        complexes_to_clear = set()
        for complex_o in self.template.data['complexes']:
            #complex_o
            complex_source_from_role = set()
            for complex_role in complex_o['complexroles']:
                role_id = complex_role['templaterole_ref'].split('/')[-1]
                complex_source_from_role.add(role_source[role_id])
            if len(complex_source_from_role) == 0:
                #print(complex_o)
                pass
            elif len(complex_source_from_role) == 1:
                if not list(complex_source_from_role)[0] == complex_o['source']:
                    ss = list(complex_source_from_role)[0]
                    logger.debug('%s %s', ss, complex_o['source'])
                    complex_o['source'] = ss
            else:
                print(complex_o)
            if not complex_o['source'] == source_allow:
                complexes_to_clear.add(complex_o['id'])

        reactions_to_clear = set()
        for reaction_o in self.template.data['reactions']:
            templatecomplex_refs = reaction_o['templatecomplex_refs']
            templatecomplex_refs_filter = list(filter(
                lambda x : not x.split('/')[-1] in complexes_to_clear, 
                templatecomplex_refs))
            if not len(templatecomplex_refs_filter) == len(templatecomplex_refs):
                logger.debug('[%s] removing complexes', reaction_o['id'])
                reaction_o['templatecomplex_refs'] = templatecomplex_refs_filter
            if len(templatecomplex_refs) == 0:
                reactions_to_clear.add(reaction_o['id'])

        template_reactions_filter = list(filter(lambda x : not x['id'] in reactions_to_clear, self.template.data['reactions']))

        return template_reactions_filter

def add_role_rxn(trxn, functions):
    for function_id in functions:
        n = annotation_api.neo4j_graph.nodes[int(function_id)]
        nfunction = Neo4jAnnotationFunction(n)
        sn = normalize_role(nfunction.value)
        role_id = function_id
        if sn in search_name_to_role_id:
            role_id = search_name_to_role_id[sn]
        if len(nfunction.sub_functions) == 0:
            #check if role in rxn
            cpx_roles = trxn.get_complex_roles()
            match = dict(filter(lambda x : role_id in x[1], cpx_roles.items()))
            if len(match) == 0:
                template_cpx_id = template.get_complex_from_role(set([role_id]))
                if template_cpx_id == None:
                    new_role_id, template_cpx_id = template.add_solo_role_with_complex(nfunction.value)
                    #print('+', trxn.id, new_role_id, template_cpx_id, role_id, nfunction.value)
                #trxn.data['templatecomplex_refs'].append('~/complexes/id/' + template_cpx_id)

def report(annotation_api, user_id):
    for rxn_id in a['fungi']:
        for function_id in a['fungi'][rxn_id]['current']:
            action = a['fungi'][rxn_id]['current'][function_id]
            if user_id in a['fungi'][rxn_id]['user'][int(function_id)]:
                role_str = annotation_api.matcher.get(int(function_id))['key']
                ss = "{}\t{}\t{}\t{}".format(rxn_id, role_str, action, a['fungi'][rxn_id]['user'][int(function_id)])
                print(ss)

def get_curation_data_(doc):
    
    functions = doc['functions']
    function_user_data = {}
    for l in doc['log']:
        target = l['target']
        user_id = l['user_id']
        t = l['timestamp']
        action = l['action']
        if not target in function_user_data:
            function_user_data[target] = {}
        if not user_id in function_user_data[target]:
            function_user_data[target][user_id] = (action, t)
        else:
            prev_t = function_user_data[target][user_id][1]
            if prev_t < t:
                function_user_data[target][user_id] = (action, t)
    return functions, function_user_data

def get_curation_data(template_set_id, a):
    accept_scores = set([
        #'opt_score3', #*
        #'opt_score2', #**
        'opt_score1', #***
    ])
    remove = {}
    accept = {}
    for rxn_id in a[template_set_id]:
        remove[rxn_id] = set()
        accept[rxn_id] = set()
        mapping = a[template_set_id][rxn_id]['current']
        for function_id in mapping:
            if mapping[function_id] in accept_scores:
                accept[rxn_id].add(function_id)
            else:
                remove[rxn_id].add(function_id)
                
    return accept, remove

def get_function(function_id, annotation_api):
    n = annotation_api.neo4j_graph.nodes[int(function_id)]
    nfunction = Neo4jAnnotationFunction(n)
    sn = normalize_role(nfunction.value)
    role_id = function_id
    if sn in search_name_to_role_id:
        role_id = search_name_to_role_id[sn]
    #print(function_id, role_id, nfunction, sn)
    return nfunction, role_id

def remove_role(trxn, role_id):
    complex_roles = trxn.get_complex_roles()
    delete_set = set()
    for complex_id in complex_roles:
        if role_id in complex_roles[complex_id]:
            delete_set.add('~/complexes/id/' + complex_id)

    templatecomplex_refs = list(filter(
        lambda x : not x in delete_set, 
        trxn.data['templatecomplex_refs']))
    
    return templatecomplex_refs

def add_role(trxn, role_ids):
    complex_roles = trxn.get_complex_roles()
    role_match = {}
    for o in role_ids:
        role_match[o] = False
    for complex_id in complex_roles:
        for o in role_match:
            if o in complex_roles[complex_id]:
                role_match[o] = True
    all_roles_present = True
    for o in role_match:
        all_roles_present &= role_match[o]
    if all_roles_present:
        logger.debug('ignore %s all present in atleast 1 complex', role_ids)
        return None
    complex_id = template.get_complex_from_role(role_ids)
    if complex_id == None:
        logger.warning('unable to find complex for %s', role_ids)
        return None
    complex_ref = '~/complexes/id/' + complex_id
    if complex_ref in trxn.data['templatecomplex_refs']:
        logger.debug('already contains complex %s, role %s', role_ids, complex_ref)
        return None
    return complex_ref

def get_role_change(rxn_id, test_accept, test_remove):
    rxn_role_change = {}
    for function_id in test_accept[rxn_id]:
        rxn_role_change[function_id] = True
    for function_id in test_remove[rxn_id]:
        if not function_id in rxn_role_change:
            rxn_role_change[function_id] = False
        else:
            print('!')
    return rxn_role_change

def update_roles(trxn, rxn_role_change):
    #trxn_roles = trxn.get_complex_roles()
    #for cpd_id in trxn_roles:
    #    for role_id in trxn_roles[cpd_id]:
    #        logger.warning('%s %s %s', rxn_id, role_id, role_id_to_name[role_id])
    for function_id in rxn_role_change:
        nfunction, role_id = get_function(function_id)
        if len(nfunction.sub_functions) == 0:
            if len(role_id) > 1 and rxn_role_change[function_id]:
                logger.warning('%s multiple role ids %s %s', rxn_id, nfunction, role_id)
            else:
                role_id = list(role_id)[0]
                role = template.get_role(role_id)
                if rxn_role_change[function_id]:
                    #print('accept or add')
                    templatecomplex_ref = add_role(trxn, [role_id])
                    if not templatecomplex_ref == None:
                        trxn.data['templatecomplex_refs'].append(templatecomplex_ref)
                    logger.debug('%s accept or add role %s, %s', rxn_id, nfunction, templatecomplex_ref)
                else:
                    #print('delete or ignore', role_id, role['name'])
                    templatecomplex_refs = remove_role(trxn, role_id)
                    if not templatecomplex_refs == None:
                        trxn.data['templatecomplex_refs'] = templatecomplex_refs
                    logger.debug('%s delete role %s, removed %d complex(es)', rxn_id, nfunction, len(trxn.data['templatecomplex_refs']) - len(templatecomplex_refs))                
                #print(('+' if rxn_role_change[function_id] else '-') + function_id, nfunction, role_id, role['source'])
        else:
            logger.debug('%s ignore multifunction role', rxn_id)

#'/Users/fliu/workspace/jupyter/web/annotation/data/TempModels/MitoCore.json'
def aaaaaa(f):
    mmm = None
    with open(f, 'r') as fh:
        mmm = json.loads(fh.read())
    for o in mmm['metabolites']:
        o['id'] += '@MitoCore'
    for o in mmm['reactions']:
        o['id'] += '@MitoCore'
        o['metabolites'] = dict(map(lambda x : (x[0] + '@MitoCore', x[1]), o['metabolites'].items()))

    with open(f, 'w') as fh:
        fh.write(json.dumps(mmm))