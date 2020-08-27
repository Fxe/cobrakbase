

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

    def summary(self):
        role_source = {}
        role_source_count = {}
        complex_source = {}
        complex_source_count = {}
        reaction_source_count = {}
        for role in self.template.data['roles']:
            role_source[role['id']] = role['source']
            if role['source'] not in role_source_count:
                role_source_count[role['source']] = 0
            role_source_count[role['source']] += 1
        for cpx in self.template.data['complexes']:
            cpx_source = set()
            for complex_role in cpx['complexroles']:
                role_id = complex_role['templaterole_ref'].split('/')[-1]
                cpx_source.add(role_source[role_id])
            complex_source[cpx['id']] = cpx_source
            cpx_source = ';'.join(sorted(list(cpx_source)))
            if cpx_source not in complex_source_count:
                complex_source_count[cpx_source] = 0
            complex_source_count[cpx_source] += 1
        for rxn in self.template.data['reactions']:
            rxn_source = set()
            for complex_ref in rxn['templatecomplex_refs']:
                complex_id = complex_ref.split('/')[-1]
                rxn_source |= complex_source[complex_id]
            rxn_source = ';'.join(sorted(list(rxn_source)))
            if rxn_source not in reaction_source_count:
                reaction_source_count[rxn_source] = 0
            reaction_source_count[rxn_source] += 1
        print('Role Source Summary')
        for s in role_source_count:
            print(s, role_source_count[s])
        print('\nComplex Role Source Summary')
        for s in complex_source_count:
            print(s, complex_source_count[s])
        print('\nReaction Complex Role Summary')
        for s in reaction_source_count:
            print(s, reaction_source_count[s])

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