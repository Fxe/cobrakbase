from cobrakbase.core.kbaseobject import KBaseObject, KBaseObjectBase, AttrDict
from cobrakbase.core.utils import get_id_from_ref
from cobrakbase.core.kbasegenomesgenome import normalize_role
from cobrakbase.core.kbasefba.new_template_reaction import NewModelTemplateReaction


class TemplateRole(KBaseObjectBase):
    
    def __init__(self, data, template=None):
        super().__init__(data)
        self.template = template


class NewModelTemplate(KBaseObject):
    
    def __init__(self, data=None, info=None, args=None, role_suf='ftr', complex_suf='cpx'):
        super().__init__(data, info, args)
        self.role_suf = role_suf
        self.complex_suf = complex_suf
        self.role_last_id = self.get_last_id_value(self.data['roles'], role_suf)
        self.complex_last_id = self.get_last_id_value(self.data['complexes'], complex_suf)
        
        self.role_set_to_cpx = {}
        self.search_name_to_role_id = {}
        for role in self.data['roles']:
            self.search_name_to_role_id[normalize_role(role['name'])] = role['id']
        for cpx in self.data['complexes']:
            roles = set()
            for complexrole in cpx['complexroles']:
                role_id = complexrole['templaterole_ref'].split('/')[-1]
                roles.add(role_id)
            #print(cpx, roles)
            self.role_set_to_cpx[';'.join(sorted(roles))] = cpx['id']
        
    def get_role_sources(self):
        pass
    
    def get_complex_sources(self):
        pass
        
    def get_complex_from_role(self, roles):
        cpx_role_str = ';'.join(sorted(roles))
        if cpx_role_str in self.role_set_to_cpx:
            return self.role_set_to_cpx[cpx_role_str]
        return None
        
    def add_role(self, name, source='ModelSEED'):
        sn = normalize_role(name)
        if sn in self.search_name_to_role_id:
            return self.search_name_to_role_id[sn]
        self.role_last_id += 1
        role_id = self.role_suf + str(self.role_last_id).zfill(5)
        self.roles += [AttrDict({
            'aliases': [],
            'features': [],
            'id': role_id,
            'name': name,
            'source': source
        })]
        self.search_name_to_role_id[sn] = role_id
        return role_id
    
    def add_complex_from_role_names(self, role_names, source='ModelSEED'):
        role_ids = set(map(lambda o: self.add_role(o, source), role_names))
        complex_id = self.get_complex_from_role(role_ids)
        if complex_id is None:
            self.complex_last_id += 1
            complex_id = self.complex_suf + str(self.complex_last_id).zfill(5)
            complex_data = {
                'complexroles': [],
                'confidence': 0,
                'id': complex_id,
                'name': complex_id,
                'reference': 'null',
                'source': source
            }
            for role_id in role_ids:
                complex_data['complexroles'].append({
                    'optional_role': 0,
                    'templaterole_ref': '~/roles/id/' + role_id,
                    'triggering': 1
                })

            # print(complex_data)
            self.complexes += [AttrDict(complex_data)]
            self.role_set_to_cpx[';'.join(sorted(role_ids))] = complex_id
            
        return complex_id
        
    def add_solo_role_with_complex(self, name):
        role_id = self.add_role(name)
        complex_id = self.add_complex_from_role_names([name])
        return role_id, complex_id
        
    def get_last_id_value(self, l, s):
        last_id = 0
        for o in l:
            id = o['id']
            if id.startswith(s):
                number_part = id[len(s):]
                if len(number_part) == 5:
                    if int(number_part) > last_id:
                        last_id = int(number_part)
        return last_id

    def get_complex(self, id):
        return self.complexes.get_by_id(id)

    def get_reaction(self, id):
        return self.reactions.get_by_id(id)

    def get_role(self, id):
        return self.roles.get_by_id(id)

    def _to_object(self, key, data):
        if key == 'reactions':
            return NewModelTemplateReaction(data, self)
        return super()._to_object(key, data)
