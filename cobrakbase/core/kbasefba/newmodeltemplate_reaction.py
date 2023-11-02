import copy
from enum import Enum
import math
from cobra.core import Reaction
from cobra.core.dictlist import DictList
from modelseedpy.core.mstemplate import MSTemplateReaction
from modelseedpy.core.msmodel import (
    get_direction_from_constraints,
    get_reaction_constraints_from_direction,
    get_cmp_token,
)
from cobrakbase.modelseed.modelseed_reaction import to_str2


class TemplateReactionType(Enum):
    CONDITIONAL = "conditional"
    UNIVERSAL = "universal"
    SPONTANEOUS = "spontaneous"
    GAPFILLING = "gapfilling"


class NewModelTemplateReaction(MSTemplateReaction):
    def __init__(
        self,
        rxn_id: str,
        reference_id: str,
        name="",
        subsystem="",
        lower_bound=0.0,
        upper_bound=None,
        reaction_type=TemplateReactionType.CONDITIONAL,
        gapfill_direction="=",
        base_cost=1000,
        reverse_penalty=1000,
        forward_penalty=1000,
    ):
        """

        :param rxn_id:
        :param reference_id:
        :param name:
        :param subsystem:
        :param lower_bound:
        :param upper_bound:
        :param reaction_type:
        :param gapfill_direction:
        :param base_cost:
        :param reverse_penalty:
        :param forward_penalty:
        :param status:
        """
        super().__init__(
            rxn_id,
            reference_id,
            name,
            subsystem,
            lower_bound,
            upper_bound,
            reaction_type,
            gapfill_direction,
            base_cost,
            reverse_penalty,
            forward_penalty,
            None,
        )

    @property
    def gene_reaction_rule(self):
        return " or ".join(map(lambda x: x.id, self.complexes))

    @gene_reaction_rule.setter
    def gene_reaction_rule(self, gpr):
        pass

    @property
    def compartment(self):
        """

        :return:
        """
        return get_cmp_token(self.compartments)

    @staticmethod
    def from_dict(d, template):
        metabolites = {}
        complexes = set()
        for o in d["templateReactionReagents"]:
            comp_compound = template.compcompounds.get_by_id(
                o["templatecompcompound_ref"].split("/")[-1]
            )
            metabolites[comp_compound] = o["coefficient"]
        for o in d["templatecomplex_refs"]:
            protein_complex = template.complexes.get_by_id(o.split("/")[-1])
            complexes.add(protein_complex)
        lower_bound, upper_bound = get_reaction_constraints_from_direction(
            d["direction"]
        )
        if "lower_bound" in d and "upper_bound" in d:
            lower_bound = d["lower_bound"]
            upper_bound = d["upper_bound"]
        reaction = NewModelTemplateReaction(
            d["id"],
            d["reaction_ref"].split("/")[-1],
            d["name"],
            "",
            lower_bound,
            upper_bound,
            d["type"],
            d["GapfillDirection"],
            d["base_cost"],
            d["reverse_penalty"],
            d["forward_penalty"],
        )
        reaction.add_metabolites(metabolites)
        reaction.add_complexes(complexes)
        return reaction

    def add_complexes(self, complex_list):
        self.complexes += complex_list

    @property
    def cstoichiometry(self):
        return dict(
            ((met.id, met.compartment), coefficient)
            for (met, coefficient) in self.metabolites.items()
        )

    def remove_role(self, role_id):
        pass

    def remove_complex(self, complex_id):
        pass

    def get_roles(self):
        """

        :return:
        """
        roles = set()
        for cpx in self.complexes:
            for role in cpx.roles:
                roles.add(role)
        return roles

    def get_complexes(self):
        return self.complexes

    def get_complex_roles(self):
        res = {}
        for complexes in self.data["templatecomplex_refs"]:
            complex_id = complexes.split("/")[-1]
            res[complex_id] = set()
            if self._template:
                cpx = self._template.get_complex(complex_id)

                if cpx:
                    for complex_role in cpx["complexroles"]:
                        role_id = complex_role["templaterole_ref"].split("/")[-1]
                        res[complex_id].add(role_id)
                else:
                    print("!!")
        return res

    def get_data(self):
        template_reaction_reagents = list(
            map(
                lambda x: {
                    "coefficient": x[1],
                    "templatecompcompound_ref": "~/compcompounds/id/" + x[0].id,
                },
                self.metabolites.items(),
            )
        )
        return {
            "id": self.id,
            "name": self.name,
            "GapfillDirection": self.GapfillDirection,
            "base_cost": self.base_cost,
            "reverse_penalty": self.reverse_penalty,
            "forward_penalty": self.forward_penalty,
            # 'deltaG': self.deltaG,
            # 'deltaGErr': self.deltaGErr,
            "upper_bound": self.upper_bound,
            "lower_bound": self.lower_bound,
            "direction": get_direction_from_constraints(
                self.lower_bound, self.upper_bound
            ),
            "maxforflux": self.upper_bound,
            "maxrevflux": 0 if self.lower_bound > 0 else math.fabs(self.lower_bound),
            "reaction_ref": "kbase/default/reactions/id/" + self.reference_id,
            "templateReactionReagents": template_reaction_reagents,
            "templatecompartment_ref": "~/compartments/id/" + self.compartment,
            "templatecomplex_refs": sorted(
                ["~/complexes/id/" + x.id for x in self.complexes]
            ),
            "type": self.type,
        }

    # def build_reaction_string(self, use_metabolite_names=False, use_compartment_names=None):
    #    cpd_name_replace = {}
    #    if use_metabolite_names:
    #        if self._template:
    #            for cpd_id in set(map(lambda x: x[0], self.cstoichiometry)):
    #                name = cpd_id
    #                if cpd_id in self._template.compcompounds:
    #                    ccpd = self._template.compcompounds.get_by_id(cpd_id)
    #                    cpd = self._template.compounds.get_by_id(ccpd['templatecompound_ref'].split('/')[-1])
    #                    name = cpd.name
    #                cpd_name_replace[cpd_id] = name
    #        else:
    #            return self.data['definition']
    #    return to_str2(self, use_compartment_names, cpd_name_replace)

    # def __str__(self):
    #    return "{id}: {stoichiometry}".format(
    #        id=self.id, stoichiometry=self.build_reaction_string())
