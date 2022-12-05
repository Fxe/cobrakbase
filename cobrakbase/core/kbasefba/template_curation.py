import logging
from modelseedpy.core.msgenome import normalize_role
from modelseedpy.core.msmodel import get_reaction_constraints_from_direction

logger = logging.getLogger(__name__)


class TemplateCuration:
    def __init__(self, template, curation_api, annotation_api):
        self.template = template
        self.curation_api = curation_api
        self.annotation_api = annotation_api

    @staticmethod
    def get_function_user_data(doc):
        functions = doc["functions"]
        function_user_data = {}
        for log_data in doc["log"]:
            target = log_data["target"]
            user_id = log_data["user_id"]
            t = log_data["timestamp"]
            action = log_data["action"]
            if target not in function_user_data:
                function_user_data[target] = {}
            if user_id not in function_user_data[target]:
                function_user_data[target][user_id] = (action, t)
            else:
                prev_t = function_user_data[target][user_id][1]
                if prev_t < t:
                    function_user_data[target][user_id] = (action, t)
        return functions, function_user_data

    @staticmethod
    def get_user(user_log):
        res = None
        last = 0
        for user_id in user_log:
            if user_log[user_id][1] > last:
                last = user_log[user_id][1]
                res = user_id
        return res

    @staticmethod
    def filter_ignore(accept, ignore):
        res = {}
        for rxn_id in accept:
            if rxn_id not in ignore:
                res[rxn_id] = accept[rxn_id]
            else:
                res[rxn_id] = set(accept[rxn_id]) - ignore[rxn_id]
        return res

    def list_curation_reactions(self, namespace=None, filter_bad_records=True):
        for doc in self.curation_api["templates_reactions"].find():
            template_rxn_id, template_id = doc["_id"].split("@")
            if template_id == namespace or namespace is None:
                if filter_bad_records:
                    if (
                        "cmp" in doc
                        and "annotation" in doc
                        and "seed__DOT__reaction" in doc["annotation"]
                    ):
                        yield doc
                else:
                    yield doc

    def get_ignore_set_of_non_modelseed(self, reaction_annotation):
        old_rxn_ids = set(map(lambda x: x.id, self.template.reactions))
        ignore = {}
        for rxn_id in reaction_annotation:
            if rxn_id in old_rxn_ids:
                ignore[rxn_id] = set()
                t_rxn = self.template.reactions.get_by_id(rxn_id)
                id_to_source = {}
                for cpx in t_rxn.complexes:
                    for role in cpx.roles:
                        f = self.annotation_api.get_function(role.name)
                        id_to_source[f.id] = role.source
                for k in reaction_annotation[rxn_id]["current"]:
                    # function = annotation_api.get_function_by_uid(k)
                    # score = reaction_annotation['fungi'][rxn_id]['current'][k]
                    a = reaction_annotation[rxn_id]["user"][int(k)]
                    user_id = self.get_user(a)
                    if int(k) in id_to_source:
                        if (
                            user_id == "system"
                            and not id_to_source[int(k)] == "ModelSEED"
                        ):
                            ignore[rxn_id].add(k)
                            # print(rxn_id, k, score, user_id, id_to_source[int(k)], function.value)
                    # print(k, score, a, function.value, id_to_source[int(k)])
        return ignore

    def get_disabled_reactions(self, template_id):
        res = set()
        for doc in self.curation_api["templates_reactions"].find():
            rxn_id, rxn_template_id = doc["_id"].split("@")
            if rxn_template_id == template_id:
                attr = doc["attributes"]
                if "active" in attr and not doc["attributes"]["active"]:
                    res.add(rxn_id)
        return res

    def get_reaction_attributes(self, template_id):
        res = {}
        for doc in self.curation_api["templates_reactions"].find():
            rxn_id, rxn_template_id = doc["_id"].split("@")
            if rxn_template_id == template_id:
                attr = doc["attributes"]
                res[rxn_id] = attr
        return res

    def get_reaction_annotation(self):
        a = {}
        for doc in self.curation_api["templates_reactions"].find():
            rxn_id, template_id = doc["_id"].split("@")
            functions, function_user_data = self.get_function_user_data(doc)
            if template_id not in a:
                a[template_id] = {}
            a[template_id][rxn_id] = {"current": functions, "user": function_user_data}
        return a

    def get_curation_data(self, template_set_id, accept_scores=None):
        a = self.get_reaction_annotation()
        if accept_scores is None:
            accept_scores = {
                # 'opt_score3', # *
                # 'opt_score2', # **
                "opt_score1"  # ***
            }
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

    def get_function(self, function_id, search_name_to_role_id):
        gene_function = self.annotation_api.get_function_by_uid(int(function_id))
        sn = normalize_role(gene_function.value)
        # sn = nfunction.search_value
        role_id = function_id
        if sn in search_name_to_role_id:
            role_id = search_name_to_role_id[sn]
        # print(function_id, role_id, nfunction, sn)
        return gene_function, role_id

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
                print(
                    role_id,
                    list(
                        map(lambda x: self.template.roles.get_by_id(x).source, role_id)
                    ),
                )

        sn_to_roles = {}
        for role_name in roles_to_add:
            sn = normalize_role(role_name)
            if sn not in sn_to_roles:
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
                    print("!")
        return rxn_role_change

    def add_role(self, template_rxn, role_ids, auto_complex=False):
        complex_roles = template_rxn.get_complex_roles()
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
            logger.debug("ignore %s all present in atleast 1 complex", role_ids)
            return None
        complex_id = self.template.get_complex_from_role(role_ids)
        if complex_id is None:
            logger.warning("unable to find complex for %s", role_ids)
            if auto_complex:
                role_names = set()
                for role_id in role_ids:
                    role = self.template.get_role(role_id)
                    role_names.add(role["name"])
                logger.warning("build complex for %s", role_names)
                complex_id = self.template.add_complex_from_role_names(role_names)
            else:
                return None
        complex_ref = "~/complexes/id/" + complex_id
        if complex_ref in template_rxn.data["templatecomplex_refs"]:
            logger.debug("already contains complex %s, role %s", role_ids, complex_ref)
            return None
        return complex_ref

    @staticmethod
    def remove_role2(t_rxn, role_id):
        delete_set = set()
        for cpx in t_rxn.complexes:
            for role in cpx.roles:
                if role.id == role_id:
                    delete_set.add(cpx)
        for cpx in delete_set:
            t_rxn.complexes.remove(cpx)

        return t_rxn

    @staticmethod
    def remove_role(trxn, role_id):
        complex_roles = trxn.get_complex_roles()

        delete_set = set()  # Collect complexes to remove
        for complex_id in complex_roles:
            if role_id in complex_roles[complex_id]:
                delete_set.add("~/complexes/id/" + complex_id)

        # build new complex set
        complex_refs = list(
            filter(lambda x: x not in delete_set, trxn.templatecomplex_refs)
        )

        # clear and assingn new complex set
        trxn.templatecomplex_refs.clear()
        trxn.templatecomplex_refs += complex_refs

        return trxn.templatecomplex_refs

    def update_attributes(self, annotation_namespace):
        """

        :param annotation_namespace:
        :return:
        """
        reaction_attributes = self.get_reaction_attributes(
            annotation_namespace
        )  # get attributes
        for template_rxn in self.template.reactions:
            if template_rxn.id in reaction_attributes:
                attr = reaction_attributes[template_rxn.id]
                if "type" in attr:
                    template_rxn.type = attr["type"]
                if "direction" in attr:
                    lb, ub = get_reaction_constraints_from_direction(attr["direction"])
                    template_rxn.lower_bound = lb
                    template_rxn.upper_bound = ub
                if "gapfill_direction" in attr:
                    template_rxn.GapfillDirection = attr["gapfill_direction"]
                if "base_cost" in attr:
                    template_rxn.base_cost = attr["base_cost"]
                if "forward_penalty" in attr:
                    template_rxn.forward_penalty = attr["forward_penalty"]
                if "reverse_penalty" in attr:
                    template_rxn.reverse_penalty = attr["reverse_penalty"]

    def update_roles(
        self, trxn, rxn_role_change, search_name_to_role_id, auto_complex=False
    ):
        # trxn_roles = trxn.get_complex_roles()
        # for cpd_id in trxn_roles:
        #     for role_id in trxn_roles[cpd_id]:
        #         logger.warning('%s %s %s', rxn_id, role_id, role_id_to_name[role_id])
        for function_id in rxn_role_change:
            nfunction, role_id = self.get_function(function_id, search_name_to_role_id)
            if type(role_id) == int or type(role_id) == str:
                logger.debug(
                    "%s function not in template [%s] %s", trxn.id, nfunction, role_id
                )
            elif len(nfunction.sub_functions) == 0:
                if len(role_id) > 1 and rxn_role_change[function_id]:
                    logger.warning(
                        "%s multiple role ids %s %s", trxn.id, nfunction, role_id
                    )
                else:
                    role_id = list(role_id)[0]
                    # role = self.template.get_role(role_id)
                    if rxn_role_change[function_id]:
                        # print('accept or add')
                        templatecomplex_ref = self.add_role(
                            trxn, [role_id], auto_complex
                        )
                        if templatecomplex_ref is not None:
                            logger.debug(
                                "%s add templatecomplex_ref: [%s]",
                                trxn.id,
                                templatecomplex_ref,
                            )
                            trxn.data["templatecomplex_refs"].append(
                                templatecomplex_ref
                            )
                        logger.debug(
                            "%s accept or add role %s, %s",
                            trxn.id,
                            nfunction,
                            templatecomplex_ref,
                        )
                    else:
                        # print('delete or ignore', role_id, role['name'])
                        templatecomplex_refs = self.remove_role(trxn, role_id)
                        # if templatecomplex_refs is not None:
                        #    trxn.data['templatecomplex_refs'] = templatecomplex_refs
                        logger.debug(
                            "%s delete role %s, removed %d complex(es)",
                            trxn.id,
                            nfunction,
                            len(trxn.data["templatecomplex_refs"])
                            - len(templatecomplex_refs),
                        )
                        # print(('+' if rxn_role_change[function_id] else '-') + function_id, nfunction, role_id, role['source'])
            else:
                logger.debug("%s ignore multifunction role", trxn.id)

    def add_role2(self, tm, template_rxn, role_ids, auto_complex=False):
        complex_roles = {}
        for cpx in template_rxn.complexes:
            complex_roles[cpx.id] = set()
            for role in cpx.roles:
                complex_roles[cpx.id].add(role.id)
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
            logger.debug("ignore %s all present in atleast 1 complex", role_ids)
            return None
        complex_id = tm.get_complex_from_role(role_ids)
        # print(role_ids, complex_id)
        if complex_id is None:
            logger.debug("unable to find complex for %s", role_ids)
            if auto_complex:
                role_names = set()
                for role_id in role_ids:
                    role = self.template.roles.get_by_id(role_id)
                    role_names.add(role.name)
                logger.debug("build complex for %s", role_names)
                # print(role_names)
                complex_id = tm.add_complex_from_role_names(role_names)
            else:
                return None
        cpx = self.template.complexes.get_by_id(complex_id)
        if cpx in template_rxn.complexes:
            logger.debug("already contains complex %s, role %s", cpx, role_ids)
            return None
        return cpx

    def update_roles2(
        self, tm, trxn, rxn_role_change, search_name_to_role_id, auto_complex=False
    ):
        # trxn_roles = trxn.get_complex_roles()
        # for cpd_id in trxn_roles:
        #     for role_id in trxn_roles[cpd_id]:
        #         logger.warning('%s %s %s', rxn_id, role_id, role_id_to_name[role_id])
        for function_id in rxn_role_change:
            nfunction, role_id = self.get_function(function_id, search_name_to_role_id)
            if type(role_id) == int or type(role_id) == str:
                logger.debug(
                    "%s function not in template [%s] %s", trxn.id, nfunction, role_id
                )
            elif len(nfunction.sub_functions) == 0:
                if len(role_id) > 1 and rxn_role_change[function_id]:
                    logger.warning(
                        "%s multiple role ids %s %s", trxn.id, nfunction, role_id
                    )
                else:
                    role_id = list(role_id)[0]
                    # role = self.template.get_role(role_id)
                    if rxn_role_change[function_id]:
                        # print('accept or add', role_id, trxn)
                        cpx = self.add_role2(tm, trxn, [role_id], auto_complex)
                        if cpx is not None:
                            logger.debug(
                                "%s add templatecomplex_ref: [%s]", trxn.id, cpx
                            )
                            # print(cpx, type(trxn.complexes))
                            trxn.complexes.add(cpx)
                        logger.debug(
                            "%s accept or add role %s, %s", trxn.id, nfunction, cpx
                        )
                    else:
                        template_complexes = trxn.complexes
                        template_complexes_after = self.remove_role2(trxn, role_id)
                        # if templatecomplex_refs is not None:
                        #    trxn.data['templatecomplex_refs'] = templatecomplex_refs
                        logger.warning(
                            "%s delete role %s, removed %d complex(es)",
                            trxn.id,
                            nfunction.value,
                            len(template_complexes) - len(template_complexes_after),
                        )
                        # print(('+' if rxn_role_change[function_id] else '-') + function_id, nfunction, role_id, role['source'])
            else:
                logger.debug("%s ignore multifunction role", trxn.id)
