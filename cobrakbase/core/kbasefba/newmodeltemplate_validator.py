def validate_enum(o, k, values):
    if k in o:
        if o[k] in values:
            pass
        else:
            print("!!")
    else:
        print("!")


def validate_type(o, k, t):
    if k in o:
        if type(o[k]) is t:
            pass
        else:
            print("!!!", k, type(o[k]))
    else:
        print("!")


def validate_types(o, k, tt):
    if k in o:
        if type(o[k]) in tt:
            pass
        else:
            print("!!!", k, type(o[k]))
    else:
        print("!")


def validate_template_reaction(o):
    validate_enum(o, "GapfillDirection", [">", "<", "="])
    validate_enum(o, "direction", [">", "<", "="])
    validate_types(o, "base_cost", [int, float])
    validate_types(o, "forward_penalty", [int, float])
    validate_types(o, "reverse_penalty", [int, float])
    validate_types(o, "maxforflux", [int, float])
    validate_types(o, "maxrevflux", [int, float])
    validate_type(o, "id", str)
    validate_type(o, "name", str)
    validate_type(o, "reaction_ref", str)
    validate_type(o, "type", str)
    validate_type(o, "templatecompartment_ref", str)
    validate_type(o, "templatecomplex_refs", list)
    validate_type(o, "templateReactionReagents", list)


# for r in template_broken['reactions']:
#    validate_template_reaction(r)


class NewModelTemplateValidator:
    """
    Validate NewModelTemplate should be implemented for the json only
    NewModelTemplate should not allow undeclared references
    """

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
        for role in self.template.roles:
            role_source[role.id] = role.source
            if role.source not in role_source_count:
                role_source_count[role.source] = 0
            role_source_count[role.source] += 1
        for cpx in self.template.complexes:
            cpx_source = set()
            for role in cpx.roles:
                cpx_source.add(role_source[role.id])
            complex_source[cpx.id] = cpx_source
            cpx_source = ";".join(sorted(list(cpx_source)))
            if cpx_source not in complex_source_count:
                complex_source_count[cpx_source] = 0
            complex_source_count[cpx_source] += 1
        for rxn in self.template.data["reactions"]:
            rxn_source = set()
            for complex_ref in rxn["templatecomplex_refs"]:
                complex_id = complex_ref.split("/")[-1]
                rxn_source |= complex_source[complex_id]
            rxn_source = ";".join(sorted(list(rxn_source)))
            if rxn_source not in reaction_source_count:
                reaction_source_count[rxn_source] = 0
            reaction_source_count[rxn_source] += 1
        print("Role Source Summary")
        for s in role_source_count:
            print(s, role_source_count[s])
        print("\nComplex Role Source Summary")
        for s in complex_source_count:
            print(s, complex_source_count[s])
        print("\nReaction Complex Role Summary")
        for s in reaction_source_count:
            print(s, reaction_source_count[s])

    def validate_compounds(self):
        for o in self.template.compounds:
            continue
            # for k in o:
            #    if type(o) == float and not o[k] == o[k]:
            #        print(k)

    def validate(self):
        self.reactions_comp = {}

        self.undec_roles = set()
        self.undec_compounds = set()
        self.undec_complexes = set()
        for cpx in self.template.complexes:
            for role in cpx.roles:
                if role.id not in self.template.roles:
                    self.undec_roles.add(role.id)
        for o in self.template.compcompounds:
            if o.compound:
                self.compcompounds[o.id] = (o.compound.id, o.compartment)
            else:
                self.undec_compounds.add(o.id)

        for o in self.template.reactions:
            self.reactions_comp[o.id] = set()
            """
            for r in o['templateReactionReagents']:
                cpd_ref = r['templatecompcompound_ref'].split('/')[-1]
                if cpd_ref in self.compcompounds:
                    self.reactions_comp[o['id']].add(self.compcompounds[cpd_ref][1])
                    #print(cpd_ref, compcompounds[cpd_ref])
                else:
                    print('!!', o['id'], r['templatecompcompound_ref'])
            """

            """
            for templatecomplex_ref in o.complexes:
                complex_id = templatecomplex_ref.split('/')[-1]
                if complex_id not in self.complexes:
                    self.undec_complexes.add(complex_id)
            """
