import logging
from copy import deepcopy
from cobrakbase.core.kbasefba.newmodeltemplate import NewModelTemplate
from cobrakbase.core.kbasefba.newmodeltemplate_complex import NewModelTemplateRole, NewModelTemplateComplex
from cobrakbase.core.kbasefba.newmodeltemplate_metabolite import NewModelTemplateCompound, NewModelTemplateCompCompound
from cobrakbase.core.kbasefba.newmodeltemplate_reaction import NewModelTemplateReaction
from cobrakbase.kbase_object_info import KBaseObjectInfo

logger = logging.getLogger(__name__)


class NewModelTemplateBuilder:

    def __init__(self, template_id, name='', domain='', template_type='', version=1, info=None,
                 biochemistry=None, biomasses=None, pathways=None, subsystems=None):
        self.id = template_id
        self.version = version
        self.name = name
        self.domain = domain
        self.template_type = template_type
        self.compartments = []
        self.roles = []
        self.complexes = []
        self.compounds = []
        self.compartment_compounds = []
        self.reactions = []
        self.info = info

    @staticmethod
    def from_dict(d, info: KBaseObjectInfo, args=None):
        """

        :param d:
        :param info:
        :param args:
        :return:
        """
        builder = NewModelTemplateBuilder(d['id'], d['name'], d['domain'], d['type'], d['__VERSION__'], info)
        builder.compartments = d['compartments']
        builder.roles = d['roles']
        builder.complexes = d['complexes']
        builder.compounds = d['compounds']
        builder.compartment_compounds = d['compcompounds']
        builder.reactions = d['reactions']
        return builder

    @staticmethod
    def from_template(template):
        b = NewModelTemplateBuilder()
        for o in template.compartments:
            b.compartments.append(deepcopy(o))

        return b

    def with_compound_modelseed(self, seed_id, modelseed):
        pass

    def with_role(self, template_rxn, role_ids, auto_complex=False):
        # TODO: copy from template curation
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
            logger.debug('ignore %s all present in atleast 1 complex', role_ids)
            return None
        complex_id = self.template.get_complex_from_role(role_ids)
        if complex_id is None:
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
        if complex_ref in template_rxn.data['templatecomplex_refs']:
            logger.debug('already contains complex %s, role %s', role_ids, complex_ref)
            return None
        return complex_ref

    def with_compound(self):
        pass

    def with_compound_compartment(self):
        pass

    def with_compartment(self, cmp_id, name, ph=7, index='0'):
        res = list(filter(lambda x: x['id'] == cmp_id, self.compartments))
        if len(res) > 0:
            return res[0]

        self.compartments.append({
            'id': cmp_id,
            'name': name,
            'aliases': [],
            'hierarchy': 3,  # TODO: what is this?
            'index': index,
            'pH': ph
        })

        return self

    def build(self):
        base = {
            '__VERSION__': '',
            'biochemistry_ref': '',
            'biomasses': [],
            'compartments': self.compartments,
            'compcompounds': [],
            'complexes': [],
            'compounds': [],
            'domain': '',
            'id': '',
            'name': '',
            'pathways': [],
            'reactions': [],
            'roles': [],
            'subsystems': [],
            'type': ''
        }

        template = NewModelTemplate(self.id, self.name, self.domain, self.template_type, self.version)
        template.info = self.info if self.info else KBaseObjectInfo(object_type='KBaseFBA.NewModelTemplate')
        template.add_compounds(list(map(lambda x: NewModelTemplateCompound.from_dict(x), self.compounds)))
        template.add_comp_compounds(
            list(map(lambda x: NewModelTemplateCompCompound.from_dict(x), self.compartment_compounds)))
        template.add_roles(list(map(lambda x: NewModelTemplateRole.from_dict(x), self.roles)))
        template.add_complexes(
            list(map(lambda x: NewModelTemplateComplex.from_dict(x, template), self.complexes)))
        template.add_reactions(
            list(map(lambda x: NewModelTemplateReaction.from_dict(x, template), self.reactions)))

        return template
