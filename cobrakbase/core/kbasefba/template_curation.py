import logging
from cobrakbase.core.kbasegenomesgenome import normalize_role
logger = logging.getLogger(__name__)

class TemplateCuration:
    
    def __init__(self, template, curation_api, annotation_api):
        self.template = template
        self.curation_api = curation_api
        self.annotation_api = annotation_api
        
    def get_function_user_data(self, doc):
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
    
    def get_reaction_annotation(self):
        a = {}
        for doc in self.curation_api['templates_reactions'].find():
            rxn_id, template_id = doc['_id'].split('@')
            functions, function_user_data = self.get_function_user_data(doc)
            if not template_id in a:
                a[template_id] = {}
            a[template_id][rxn_id] = {
                'current' : functions,
                'user' : function_user_data
            }
        return a
    
    def get_curation_data(self, template_set_id):
        a = self.get_reaction_annotation()
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
    
    def get_function(self, function_id, search_name_to_role_id):
        nfunction = self.annotation_api.get_function_by_uid(int(function_id))
        sn = normalize_role(nfunction.value)
        #sn = nfunction.search_value
        role_id = function_id
        if sn in search_name_to_role_id:
            role_id = search_name_to_role_id[sn]
        #print(function_id, role_id, nfunction, sn)
        return nfunction, role_id

    def get_roles_to_add(self, test_accept, search_name_to_role_id):
        accept_role_uids = set()
        for rxn_id in test_accept:
            for role_uid in test_accept[rxn_id]:
                accept_role_uids.add(role_uid)
                
        roles_to_add = set()
        for role_uid in accept_role_uids:
            nfunction, role_id = self.get_function(role_uid, search_name_to_role_id)
            if not type(role_id) == set:
                roles_to_add.add(nfunction.value)
            elif len(role_id) == 1:
                roles_to_add.add(nfunction.value)
            else:
                print(role_id, list(map(lambda x : self.template.get_role(x)['source'], role_id)))
                
        sn_to_roles = {}
        for role_name in roles_to_add:
            sn = normalize_role(role_name)
            if not sn in sn_to_roles:
                sn_to_roles[sn] = set()
            sn_to_roles[sn].add(role_name)
                
        return sn_to_roles
    
    def get_role_change(self, rxn_id, test_accept, test_remove):
        rxn_role_change = {}
        if rxn_id in test_accept:
            for function_id in test_accept[rxn_id]:
                rxn_role_change[function_id] = True
        if rxn_id in test_remove:
            for function_id in test_remove[rxn_id]:
                if not function_id in rxn_role_change:
                    rxn_role_change[function_id] = False
                else:
                    print('!')
        return rxn_role_change
    
    def add_role(self, trxn, role_ids, auto_complex = False):
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
        complex_id = self.template.get_complex_from_role(role_ids)
        if complex_id == None:
            logger.warning('unable to find complex for %s', role_ids)
            if auto_complex:
                role_names = set()
                for role_id in role_ids:
                    role = self.template.get_role(role_id)
                    role_names.add(role['name'])
                logger.warning('build complex for %s', role_names)
                complex_id = self.template.add_complex_from_role_names(role_names)
            else:
                return None
        complex_ref = '~/complexes/id/' + complex_id
        if complex_ref in trxn.data['templatecomplex_refs']:
            logger.debug('already contains complex %s, role %s', role_ids, complex_ref)
            return None
        return complex_ref
    
    def remove_role(self, trxn, role_id):
        complex_roles = trxn.get_complex_roles()
        delete_set = set()
        for complex_id in complex_roles:
            if role_id in complex_roles[complex_id]:
                delete_set.add('~/complexes/id/' + complex_id)

        templatecomplex_refs = list(filter(
            lambda x : not x in delete_set, 
            trxn.data['templatecomplex_refs']))

        return templatecomplex_refs
    
    def update_roles(self, trxn, rxn_role_change, search_name_to_role_id, auto_complex = False):
        # trxn_roles = trxn.get_complex_roles()
        # for cpd_id in trxn_roles:
        #     for role_id in trxn_roles[cpd_id]:
        #         logger.warning('%s %s %s', rxn_id, role_id, role_id_to_name[role_id])
        for function_id in rxn_role_change:
            nfunction, role_id = self.get_function(function_id, search_name_to_role_id)
            if type(role_id) == int or type(role_id) == str:
                logger.debug('%s function not in template [%s] %s', trxn.id, nfunction, role_id)
            elif len(nfunction.sub_functions) == 0:
                if len(role_id) > 1 and rxn_role_change[function_id]:
                    logger.warning('%s multiple role ids %s %s', trxn.id, nfunction, role_id)
                else:
                    role_id = list(role_id)[0]
                    # role = self.template.get_role(role_id)
                    if rxn_role_change[function_id]:
                        # print('accept or add')
                        templatecomplex_ref = self.add_role(trxn, [role_id], auto_complex)
                        if templatecomplex_ref is not None:
                            logger.debug("%s add templatecomplex_ref: [%s]", trxn.id, templatecomplex_ref)
                            trxn.data['templatecomplex_refs'].append(templatecomplex_ref)
                        logger.debug('%s accept or add role %s, %s', trxn.id, nfunction, templatecomplex_ref)
                    else:
                        # print('delete or ignore', role_id, role['name'])
                        templatecomplex_refs = self.remove_role(trxn, role_id)
                        if templatecomplex_refs is not None:
                            trxn.data['templatecomplex_refs'] = templatecomplex_refs
                        logger.debug('%s delete role %s, removed %d complex(es)', trxn.id, nfunction, len(trxn.data['templatecomplex_refs']) - len(templatecomplex_refs))                
                    # print(('+' if rxn_role_change[function_id] else '-') + function_id, nfunction, role_id, role['source'])
            else:
                logger.debug('%s ignore multifunction role', trxn.id)