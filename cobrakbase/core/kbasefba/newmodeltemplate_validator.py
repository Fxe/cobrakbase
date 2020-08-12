class NewModelTemplateValidator():
    def __init__(self, template):
        self.template = template
        self.compounds = {}
        self.compcompounds = {}
        self.reactions = {}
        self.reactions_comp = {}
        self.roles = {}
        self.complexes = {}

        self.undec_roles = set()
        self.undec_compounds = set()
        self.undec_complexes = set()

    def validate_compounds(self):
        for o in self.template.data['compounds']:
            for k in o:
                if type(o) == float and not o[k] == o[k]:
                    print(k)
        
    def validate(self):
        self.compounds = {}
        self.compcompounds = {}
        self.reactions = {}
        self.reactions_comp = {}
        self.roles = {}
        self.complexes = {}
        
        self.undec_roles = set()
        self.undec_compounds = set()
        self.undec_complexes = set()
        for o in self.template.data['roles']:
            self.roles[o['id']] = o
        for o in self.template.data['complexes']:
            self.complexes[o['id']] = o
            for complexrole in o['complexroles']:
                role_id = complexrole['templaterole_ref'].split('/')[-1]
                if not role_id in self.roles:
                    self.undec_roles.add(role_id)
        for o in self.template.data['compounds']:
            self.compounds[o['id']] = o
            
        for o in self.template.data['compcompounds']:
            cmp_id = o['templatecompartment_ref'].split('/')[-1]
            cpd_id = o['templatecompound_ref'].split('/')[-1]
            self.compcompounds[o['id']] = (cpd_id, cmp_id)
            if cpd_id not in self.compounds:
                self.undec_compounds.add(cpd_id)
                #print('!', o['id'], o['templatecompound_ref'])
                
        for o in self.template.data['reactions']:
            self.reactions[o['id']] = o
            self.reactions_comp[o['id']] = set()
            for r in o['templateReactionReagents']:
                cpd_ref = r['templatecompcompound_ref'].split('/')[-1]
                if cpd_ref in self.compcompounds:
                    self.reactions_comp[o['id']].add(self.compcompounds[cpd_ref][1])
                    #print(cpd_ref, compcompounds[cpd_ref])
                else:
                    print('!!', o['id'], r['templatecompcompound_ref'])
            for templatecomplex_ref in o['templatecomplex_refs']:
                complex_id = templatecomplex_ref.split('/')[-1]
                if complex_id not in self.complexes:
                    self.undec_complexes.add(complex_id)