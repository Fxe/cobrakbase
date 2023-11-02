import logging
from modelseedpy.core.msgenome import normalize_role
from cobrakbase.core.kbaseobject import AttrDict
from cobrakbase.core.utils import get_cmp_token
from cobrakbase.core.kbasefba.newmodeltemplate_metabolite import (
    NewModelTemplateCompCompound,
)
from cobrakbase.core.kbasefba.newmodeltemplate_metabolite import (
    NewModelTemplateCompound,
)
from cobrakbase.core.kbasefba.newmodeltemplate_complex import (
    NewModelTemplateRole,
    NewModelTemplateComplex,
)
from cobrakbase.core.kbasefba.newmodeltemplate_reaction import NewModelTemplateReaction

logger = logging.getLogger(__name__)


class TemplateManipulator:
    def __init__(self, template, modelseed_database, role_suf="ftr", complex_suf="cpx"):
        self.role_suf = role_suf
        self.complex_suf = complex_suf
        self.template = template
        self.modelseed_database = modelseed_database
        # self.template_compounds = {}
        # self.template_compcompounds = {}
        # self.template_reactions = {}
        # self.template_compartments = {}
        self.role_last_id = self.get_last_id_value(self.template.roles, role_suf)
        self.complex_last_id = self.get_last_id_value(
            self.template.complexes, complex_suf
        )
        self.role_set_to_cpx = {}
        self.search_name_to_role_id = {}
        for cpx in self.template.complexes:
            role_ids = set(x.id for x in cpx.roles)
            self.role_set_to_cpx[";".join(sorted(role_ids))] = cpx.id
        for role in self.template.roles:
            self.search_name_to_role_id[normalize_role(role.name)] = role

    @staticmethod
    def remove_role2(t_rxn, role_id):
        delete_set = set()
        for cpx in t_rxn.complexes:
            for role in cpx.roles:
                if role.id == role_id:
                    delete_set.add(cpx)
        for cpx in delete_set:
            t_rxn.complexes.remove(cpx)

        return t_rxn.complexes

    @staticmethod
    def get_last_id_value(objects, s):
        last_id = 0
        for o in objects:
            object_id = o.id
            if object_id.startswith(s):
                number_part = object_id[len(s) :]
                if len(number_part) == 5:
                    if int(number_part) > last_id:
                        last_id = int(number_part)
        return last_id

    def add_role(self, name, source="ModelSEED"):
        sn = normalize_role(name)
        if sn in self.search_name_to_role_id:
            return self.search_name_to_role_id[sn]
        self.role_last_id += 1
        role_id = self.role_suf + str(self.role_last_id).zfill(5)
        role = NewModelTemplateRole(role_id, name, source=source)
        self.template.add_roles([role])
        self.search_name_to_role_id[sn] = role
        return role

    def get_complex_from_role(self, roles):
        cpx_role_str = ";".join(sorted(roles))
        if cpx_role_str in self.role_set_to_cpx:
            return self.role_set_to_cpx[cpx_role_str]
        return None

    def add_complex_from_role_names(self, role_names, source="ModelSEED"):
        roles = set(map(lambda o: self.add_role(o, source), role_names))
        role_ids = set((map(lambda x: x.id, roles)))
        complex_id = self.get_complex_from_role(role_ids)
        if complex_id is None:
            self.complex_last_id += 1
            complex_id = self.complex_suf + str(self.complex_last_id).zfill(5)
            cpx = NewModelTemplateComplex(complex_id, complex_id, source, "null", 0)
            for role_id in role_ids:
                role = self.template.roles.get_by_id(role_id)
                cpx.add_role(role, triggering=True, optional=False)
            self.template.add_complexes([cpx])
            self.role_set_to_cpx[";".join(sorted(role_ids))] = complex_id

        return complex_id

    def add_solo_role_with_complex(self, name):
        role_id = self.add_role(name)
        complex_id = self.add_complex_from_role_names([name])
        return role_id, complex_id

    def clear_reaction_complexes(self):
        for template_rxn in self.template.reactions:
            template_rxn.templatecomplex_refs.clear()

    def clear_reactions(self):
        self.template.reactions.clear()
        self.template.reactions._dict.clear()

    def clear_roles(self):
        self.clear_complexes()
        self.template.roles.clear()
        self.template.roles._dict.clear()
        self.template.role_last_id = 0

    def clear_complexes(self):
        self.clear_reaction_complexes()
        self.template.complexes.clear()
        self.template.complexes._dict.clear()
        self.template.complex_last_id = 0

    def add_compartment(self, cmp_id, name, ph=7, index="0"):
        res = list(
            filter(lambda x: x["id"] == cmp_id, self.template.data["compartments"])
        )
        if len(res) > 0:
            return res[0]
        return {
            "id": cmp_id,
            "name": name,
            "aliases": [],
            "hierarchy": 3,
            "index": index,
            "pH": ph,
        }

    def add_compcompound(self, cpd_id, cmp_id):
        template_compound = None
        template_compcompound = None
        if cpd_id not in self.template_compounds:
            cpd = self.modelseed_database.get_seed_compound(cpd_id)
            mass = cpd.data["mass"]
            formula = cpd.data["formula"]
            template_compound = {
                "abbreviation": cpd.data["abbreviation"],
                "aliases": [],
                "defaultCharge": cpd.data["charge"],
                "deltaG": cpd.data["deltag"],
                "deltaGErr": cpd.data["deltagerr"],
                "formula": str(formula) if formula is not None else "",
                "id": cpd_id,
                "isCofactor": cpd.data["is_cofactor"],
                "mass": float(mass) if mass is not None and not mass == "None" else 0.0,
                "name": cpd.data["name"],
            }
            self.template_compounds[cpd.id] = template_compound
            self.template.data["compounds"].append(AttrDict(template_compound))
        template_compound = self.template_compounds[cpd_id]

        ccpd_id = "{}_{}".format(cpd_id, cmp_id)
        if ccpd_id not in self.template_compcompounds:
            template_compcompound = {
                "charge": template_compound["defaultCharge"],
                "id": ccpd_id,
                "maxuptake": 0,
                "templatecompartment_ref": "~/compartments/id/" + cmp_id,
                "templatecompound_ref": "~/compounds/id/" + cpd_id,
            }
            self.template_compcompounds[ccpd_id] = template_compcompound
            self.template.data["compcompounds"].append(AttrDict(template_compcompound))
        else:
            template_compcompound = self.template_compcompounds[ccpd_id]
        return template_compcompound

    def configure_stoichiometry(self, cstoichiometry, compartment_config):
        template_reaction_reagents = []
        stoich_cmps = set()
        for t in cstoichiometry:
            cpd_id = t[0]
            cmp_token = t[1]

            if not cmp_token in compartment_config:
                raise Exception("missing compartment_config for " + cmp_token)
            stoich_cmps.add(compartment_config[cmp_token])
            ccpd_id = "{}_{}".format(cpd_id, compartment_config[cmp_token])
            self.add_compcompound(cpd_id, compartment_config[cmp_token])
            templatecompcompound_ref = "~/compcompounds/id/" + ccpd_id
            template_reaction_reagents.append(
                {
                    "coefficient": cstoichiometry[t],
                    "templatecompcompound_ref": templatecompcompound_ref,
                }
            )

        return template_reaction_reagents, stoich_cmps

    def build_template_reaction_from_modelseed(
        self,
        rxn_id,
        compartment_config,
        direction=None,
        base_cost=1000,
        forward_penalty=-1000,
        reverse_penalty=-1000,
        reaction_type="conditional",
    ):
        rxn = self.modelseed_database.get_seed_reaction(rxn_id)
        if rxn is None:
            return None
        if direction is None:
            direction = rxn.data["direction"]

        template_reaction_reagents, stoich_cmps = self.configure_stoichiometry(
            rxn.cstoichiometry, compartment_config
        )
        cmp = get_cmp_token(stoich_cmps)  # calculate compartment
        self.add_compartment(cmp, cmp)

        name = rxn.data["name"]
        template_reaction = {
            "GapfillDirection": ">",
            "base_cost": base_cost,
            "direction": direction,
            "forward_penalty": forward_penalty,
            "reverse_penalty": reverse_penalty,
            "id": "{}_{}".format(rxn.id, cmp),
            "maxforflux": 100,
            "maxrevflux": -100,
            "name": rxn.id if type(name) == float or len(name.strip()) == 0 else name,
            "reaction_ref": "~/reactions/id/" + rxn.id,
            "templateReactionReagents": template_reaction_reagents,
            "templatecompartment_ref": "~/compartments/id/" + cmp,
            "templatecomplex_refs": [],
            "type": reaction_type,
        }
        return template_reaction

    def add_compcompound2(self, cpd_id, cmp_id):
        template_compound = None
        template_compcompound = None

        if cpd_id not in self.template.compounds:
            cpd = self.modelseed_database.get_seed_compound(cpd_id)
            mass = (
                float(cpd.data["mass"])
                if cpd.data["mass"] is not None and not cpd.data["mass"] == "None"
                else 0.0
            )
            formula = (
                str(cpd.data["formula"]) if cpd.data["formula"] is not None else ""
            )
            template_compound = NewModelTemplateCompound(
                cpd_id,
                formula,
                cpd.data["name"],
                cpd.data["charge"],
                mass,
                cpd.data["deltag"],
                cpd.data["deltagerr"],
                cpd.data["is_cofactor"],
                cpd.data["abbreviation"],
                [],
            )
            self.template.add_compounds([template_compound])
        template_compound = self.template.compounds.get_by_id(cpd_id)
        ccpd_id = "{}_{}".format(cpd_id, cmp_id)
        if ccpd_id not in self.template.compcompounds:
            template_compcompound = NewModelTemplateCompCompound(
                ccpd_id,
                template_compound.default_charge,
                cmp_id,
                cpd_id,
                0,
                self.template,
            )
            self.template.add_comp_compounds([template_compcompound])
        else:
            template_compcompound = self.template.compcompounds.get_by_id(ccpd_id)
        return template_compcompound

    def configure_stoichiometry2(self, cstoichiometry, compartment_config):
        # print('configure_stoichiometry2', cstoichiometry, compartment_config)
        metabolites = {}
        stoich_cmps = set()
        for (cpd_id, cmp_token), value in cstoichiometry.items():
            if not cmp_token in compartment_config:
                raise Exception("missing compartment_config for " + cmp_token)
            stoich_cmps.add(compartment_config[cmp_token])
            # print(cpd_id, cmp_token, compartment_config[cmp_token])
            ccpd_id = "{}_{}".format(cpd_id, compartment_config[cmp_token])
            self.add_compcompound2(cpd_id, compartment_config[cmp_token])
            metabolites[self.template.compcompounds.get_by_id(ccpd_id)] = value

        return metabolites, stoich_cmps

    def add_compartment2(self, cmp_id, name, ph=7, index="0"):
        res = list(filter(lambda x: x["id"] == cmp_id, self.template.compartments))
        if len(res) > 0:
            return res[0].get_data()
        return {
            "id": cmp_id,
            "name": name,
            "aliases": [],
            "hierarchy": 3,
            "index": index,
            "pH": ph,
        }

    def build_template_reaction_from_modelseed2(
        self,
        rxn_id,
        compartment_config,
        direction=None,
        base_cost=1000,
        forward_penalty=1000,
        reverse_penalty=1000,
        reaction_type="conditional",
    ):
        rxn = self.modelseed_database.get_seed_reaction(rxn_id)
        if rxn is None:
            return None
        if direction is None:
            direction = rxn.data["direction"]

        metabolites, stoich_cmps = self.configure_stoichiometry2(
            rxn.cstoichiometry, compartment_config
        )
        cmp = get_cmp_token(stoich_cmps)  # calculate compartment
        # self.add_compartment2(cmp, cmp)
        name = (
            rxn.id
            if type(rxn.data["name"]) == float or len(rxn.data["name"].strip()) == 0
            else rxn.data["name"]
        )

        template_reaction = NewModelTemplateReaction(
            f"{rxn.id}_{cmp}",
            rxn_id,
            name,
            "",
            0,
            1000,
            reaction_type,
            "=",
            base_cost,
            reverse_penalty,
            forward_penalty,
        )
        template_reaction.add_metabolites(metabolites)
        return template_reaction

    def get_role_to_rxn_ids(self):
        """
        Index of role ID mapped to reactions (Set)
        """
        role_to_rxn_ids = {}
        for template_reaction in self.template.reactions:
            for cpx in template_reaction.complexes:
                for role in cpx.roles:
                    if role.id not in role_to_rxn_ids:
                        role_to_rxn_ids[role.id] = set()
                    role_to_rxn_ids[role.id].add(template_reaction.id)

        return role_to_rxn_ids

    def get_search_name_to_role_id(self):
        """
        Maps search name to role id for duplicate role detection
        :return:
        """
        search_name_to_role_id = {}
        for role in self.template.roles:
            n = normalize_role(role.name)
            if n not in search_name_to_role_id:
                search_name_to_role_id[n] = set()
            search_name_to_role_id[n].add(role.id)
        return search_name_to_role_id

    def get_role_to_complexes(self):
        role_to_complexes = {}
        for cpx in self.template.complexes:
            for role in cpx.roles:
                if role.id not in role_to_complexes:
                    role_to_complexes[role.id] = set()
                role_to_complexes[role.id].add(cpx.id)
        return role_to_complexes

    def delete_roles(self, role_ids, clear_orphan=True):
        """
        Delete roles from template and clear complex if orphan (Optional)
        """
        role_to_complexes = self.get_role_to_complexes()
        roles_to_delete = set()
        complexes_to_delete = set()
        for role_id in role_ids:
            roles_to_delete.add(role_id)
            if role_id in role_to_complexes:
                for cpx_id in role_to_complexes[role_id]:
                    cpx = self.template.complexes.get_by_id(cpx_id)
                    # delete role_id from cpx
                    to_delete = set(
                        role.id for role in cpx.roles if role.id in role_ids
                    )
                    for i in to_delete:
                        role = self.template.roles.get_by_id(i)
                        del cpx.roles[role]
                    if clear_orphan and len(cpx.roles) == 0:
                        complexes_to_delete.add(cpx_id)

        for role_id in roles_to_delete:
            self.template.roles.remove(role_id)
        for complex_id in complexes_to_delete:
            self.template.complexes.remove(complex_id)

    def clear_orphan_roles(self):
        """
        Clean roles with conflicting search name and delete from template
        Resolves by selecting the role that is used in a reaction
          outputs warning if unable to select
          (e.g., two or more roles conflict but both used in reactions).
        """
        role_to_rxn_ids = self.get_role_to_rxn_ids()
        search_name_to_role_id = self.get_search_name_to_role_id()

        to_delete = set()
        to_update = set()
        for sn in search_name_to_role_id:
            role_ids = list(sorted(search_name_to_role_id[sn]))
            if len(search_name_to_role_id[sn]) > 1:
                selected = []
                for role_id in role_ids:
                    rxn_count = (
                        len(role_to_rxn_ids[role_id])
                        if role_id in role_to_rxn_ids
                        else 0
                    )
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
                            role.aliases.append("alias:" + other_role.name)
                else:
                    logger.warning("unable to select role %s", role_ids)

        self.delete_roles(to_delete, True)

        return to_update, to_delete

    def clean_template(self, white_list=None):
        """
        Remove roles and complexes from reactions not in the whitelist
        """
        if white_list is None:
            white_list = ["ModelSEED"]
        # search_name_to_role_id = self.get_search_name_to_role_id()

        complexes_to_clear = set()
        for cpx in self.template.complexes:
            complex_source_from_role = set(r.source for r in cpx.roles)
            if len(complex_source_from_role) == 0:
                pass
            elif len(complex_source_from_role) == 1:
                if not list(complex_source_from_role)[0] == cpx.source:
                    logger.debug("%s %s", complex_source_from_role, cpx.source)
                    cpx.source = complex_source_from_role.pop()
            else:
                print(cpx)
            if cpx.source not in white_list:
                complexes_to_clear.add(cpx.id)

        reactions_to_clear = set()
        for reaction in self.template.reactions:
            cpxs = set(c.id for c in reaction.complexes)
            if len(cpxs & complexes_to_clear) > 0:
                for cpx in {
                    self.template.complexes.get_by_id(i)
                    for i in cpxs & complexes_to_clear
                }:
                    reaction.complexes.remove(cpx)

        template_reactions_filter = list(
            filter(lambda x: x.id not in reactions_to_clear, self.template.reactions)
        )

        return template_reactions_filter

    @staticmethod
    def get_non_obsolete(rxn, db):
        for i in rxn.data["linked_reaction"].split(";"):
            other_rxn = db.get_seed_reaction(i)
            if not other_rxn.is_obsolete:
                return other_rxn

    def upgrade_obsolete2(self):
        to_delete = {}
        for t_rxn in self.template.reactions:
            rxn = self.modelseed_database.get_seed_reaction(t_rxn.reference_id)
            if rxn is not None:
                if rxn.is_obsolete:
                    correct_version = self.get_non_obsolete(
                        rxn, self.modelseed_database
                    )
                    if correct_version.is_obsolete:
                        logger.warning(
                            "[BAD   ] %s[%s] %s -> %s",
                            t_rxn.id,
                            t_rxn.reference_id,
                            rxn.id,
                            correct_version.id,
                        )
                    else:
                        to_delete[t_rxn.id] = correct_version
            else:
                logger.warning("reaction not found in database: %s", t_rxn.id)

        for t_rxn_id in to_delete:
            if t_rxn_id in self.template.reactions:
                correct_version = to_delete[t_rxn_id]
                t_rxn = self.template.reactions.get_by_id(t_rxn_id)
                logger.debug(
                    "[DELETE] %s[%s] -> %s",
                    t_rxn.id,
                    t_rxn.reference_id,
                    correct_version.id,
                )
                self.template.reactions.remove(t_rxn.id)
                id_update = t_rxn.id.split("_")
                id_update[0] = correct_version.id
                t_rxn.id = "_".join(id_update)
                t_rxn.reference_id = correct_version.id
                if (
                    t_rxn.id not in self.template.reactions
                ):  # we only add reaction back if non obsolete is missing
                    logger.debug(
                        "[ADD   ] %s[%s] -> %s",
                        t_rxn.id,
                        t_rxn.reference_id,
                        correct_version.id,
                    )
                    self.template.reactions += [t_rxn]
                else:
                    logger.debug(
                        "[SKIP  ] %s[%s] -> %s",
                        t_rxn.id,
                        t_rxn.reference_id,
                        correct_version.id,
                    )

        return to_delete

    def upgrade_obsolete(self):
        """

        :return:
        """

        if self.modelseed_database is None:
            logger.warning("missing modelseed database")
            return None
        all_template_rxn_ids = set(map(lambda x: x.id, self.template.reactions))
        updated_reactions = []
        for trxn in self.template.reactions:
            seed_rxn_id = trxn.reaction_ref.split("/")[-1]
            rxn = self.modelseed_database.get_seed_reaction(seed_rxn_id)
            if rxn is not None:
                if rxn.is_obsolete:
                    correct_version = self.get_non_obsolete(
                        rxn, self.modelseed_database
                    )
                    ref = trxn.reaction_ref.split("/")[:-1]
                    ref.append(correct_version.id)
                    ref = "/".join(ref)
                    id_update = trxn.id.split("_")
                    id_update[0] = correct_version.id
                    id_update = "_".join(id_update)

                    # non obsolete version alredy exists then it is duplicate: action delete
                    if id_update not in all_template_rxn_ids:
                        logger.warning("%s %s", rxn, correct_version)
                        trxn.id = id_update
                        trxn.reaction_ref = ref
                        all_template_rxn_ids.add(trxn.id)
            else:
                logger.warning("reaction not found in database: %s", trxn.id)
            updated_reactions.append(trxn)

        self.template.reactions.clear()
        self.template.reactions._dict.clear()
        self.template.reactions += updated_reactions


def add_role_rxn(trxn, functions):
    for function_id in functions:
        n = annotation_api.neo4j_graph.nodes[int(function_id)]
        nfunction = Neo4jAnnotationFunction(n)
        sn = normalize_role(nfunction.value)
        role_id = function_id
        if sn in search_name_to_role_id:
            role_id = search_name_to_role_id[sn]
        if len(nfunction.sub_functions) == 0:
            # check if role in rxn
            cpx_roles = trxn.get_complex_roles()
            match = dict(filter(lambda x: role_id in x[1], cpx_roles.items()))
            if len(match) == 0:
                template_cpx_id = template.get_complex_from_role(set([role_id]))
                if template_cpx_id == None:
                    new_role_id, template_cpx_id = template.add_solo_role_with_complex(
                        nfunction.value
                    )
                    # print('+', trxn.id, new_role_id, template_cpx_id, role_id, nfunction.value)
                # trxn.data['templatecomplex_refs'].append('~/complexes/id/' + template_cpx_id)


def report(annotation_api, user_id):
    for rxn_id in a["fungi"]:
        for function_id in a["fungi"][rxn_id]["current"]:
            action = a["fungi"][rxn_id]["current"][function_id]
            if user_id in a["fungi"][rxn_id]["user"][int(function_id)]:
                role_str = annotation_api.matcher.get(int(function_id))["key"]
                ss = "{}\t{}\t{}\t{}".format(
                    rxn_id,
                    role_str,
                    action,
                    a["fungi"][rxn_id]["user"][int(function_id)],
                )
                print(ss)


def get_curation_data_(doc):
    functions = doc["functions"]
    function_user_data = {}
    for l in doc["log"]:
        target = l["target"]
        user_id = l["user_id"]
        t = l["timestamp"]
        action = l["action"]
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
    accept_scores = set(
        [
            # 'opt_score3', #*
            # 'opt_score2', #**
            "opt_score1",  # ***
        ]
    )
    remove = {}
    accept = {}
    for rxn_id in a[template_set_id]:
        remove[rxn_id] = set()
        accept[rxn_id] = set()
        mapping = a[template_set_id][rxn_id]["current"]
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
    # print(function_id, role_id, nfunction, sn)
    return nfunction, role_id


def remove_role(trxn, role_id):
    complex_roles = trxn.get_complex_roles()
    delete_set = set()
    for complex_id in complex_roles:
        if role_id in complex_roles[complex_id]:
            delete_set.add("~/complexes/id/" + complex_id)

    templatecomplex_refs = list(
        filter(lambda x: not x in delete_set, trxn.data["templatecomplex_refs"])
    )

    return templatecomplex_refs


def get_role_change(rxn_id, test_accept, test_remove):
    rxn_role_change = {}
    for function_id in test_accept[rxn_id]:
        rxn_role_change[function_id] = True
    for function_id in test_remove[rxn_id]:
        if not function_id in rxn_role_change:
            rxn_role_change[function_id] = False
        else:
            print("!")
    return rxn_role_change


def update_roles(trxn, rxn_role_change):
    # trxn_roles = trxn.get_complex_roles()
    # for cpd_id in trxn_roles:
    #    for role_id in trxn_roles[cpd_id]:
    #        logger.warning('%s %s %s', rxn_id, role_id, role_id_to_name[role_id])
    for function_id in rxn_role_change:
        nfunction, role_id = get_function(function_id)
        if len(nfunction.sub_functions) == 0:
            if len(role_id) > 1 and rxn_role_change[function_id]:
                logger.warning("%s multiple role ids %s %s", rxn_id, nfunction, role_id)
            else:
                role_id = list(role_id)[0]
                role = template.get_role(role_id)
                if rxn_role_change[function_id]:
                    # print('accept or add')
                    templatecomplex_ref = add_role(trxn, [role_id])
                    if not templatecomplex_ref == None:
                        trxn.data["templatecomplex_refs"].append(templatecomplex_ref)
                    logger.debug(
                        "%s accept or add role %s, %s",
                        rxn_id,
                        nfunction,
                        templatecomplex_ref,
                    )
                else:
                    # print('delete or ignore', role_id, role['name'])
                    templatecomplex_refs = remove_role(trxn, role_id)
                    if not templatecomplex_refs == None:
                        trxn.data["templatecomplex_refs"] = templatecomplex_refs
                    logger.debug(
                        "%s delete role %s, removed %d complex(es)",
                        rxn_id,
                        nfunction,
                        len(trxn.data["templatecomplex_refs"])
                        - len(templatecomplex_refs),
                    )
                    # print(('+' if rxn_role_change[function_id] else '-') + function_id, nfunction, role_id, role['source'])
        else:
            logger.debug("%s ignore multifunction role", rxn_id)


# '/Users/fliu/workspace/jupyter/web/annotation/data/TempModels/MitoCore.json'
def aaaaaa(f):
    mmm = None
    with open(f, "r") as fh:
        mmm = json.loads(fh.read())
    for o in mmm["metabolites"]:
        o["id"] += "@MitoCore"
    for o in mmm["reactions"]:
        o["id"] += "@MitoCore"
        o["metabolites"] = dict(
            map(lambda x: (x[0] + "@MitoCore", x[1]), o["metabolites"].items())
        )

    with open(f, "w") as fh:
        fh.write(json.dumps(mmm))
