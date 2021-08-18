import logging
from cobrakbase.core.kbaseobject import KBaseObject, KBaseObjectBase, AttrDict
from cobrakbase.core.kbasegenomesgenome import normalize_role
from cobra.core.dictlist import DictList
from cobrakbase.kbase_object_info import KBaseObjectInfo
from cobrakbase.core.kbasefba.newmodeltemplate_complex import NewModelTemplateRole, NewModelTemplateComplex
from cobrakbase.core.kbasefba.newmodeltemplate_metabolite import NewModelTemplateCompound, NewModelTemplateCompCompound
from cobrakbase.core.kbasefba.newmodeltemplate_reaction import NewModelTemplateReaction

logger = logging.getLogger(__name__)


class TemplateRole(KBaseObjectBase):
    
    def __init__(self, data, template=None):
        super().__init__(data)
        self.template = template


class NewModelTemplate:
    
    def __init__(self, template_id, name='', domain='', template_type='', version=1, info=None, args=None):
        self.id = template_id
        self.__VERSION__ = version
        self.name = name
        self.domain = domain
        self.biochemistry_ref = ''
        self.template_type = template_type
        self.compartments = {}
        self.biomasses = DictList()
        self.reactions = DictList()
        self.compounds = DictList()
        self.compcompounds = DictList()
        self.roles = DictList()
        self.complexes = DictList()
        self.pathways = DictList()
        self.subsystems = DictList()
        self.info = info if info else KBaseObjectInfo(object_type='KBaseFBA.NewModelTemplate')

    def add_roles(self, roles: list):
        """

        :param roles:
        :return:
        """
        duplicates = list(filter(lambda x: x.id in self.roles, roles))
        if len(duplicates) > 0:
            logger.error("unable to add roles [%s] already present in the template", duplicates)
            return None

        for x in roles:
            x._template = self
        self.roles += roles

    def add_complexes(self, complexes: list):
        """

        :param complexes:
        :return:
        """
        duplicates = list(filter(lambda x: x.id in self.complexes, complexes))
        if len(duplicates) > 0:
            logger.error("unable to add comp compounds [%s] already present in the template", duplicates)
            return None

        roles_to_add = []
        for x in complexes:
            x._template = self
            roles_rep = {}
            for role in x.roles:
                r = role
                if role.id not in self.roles:
                    roles_to_add.append(role)
                else:
                    r = self.roles.get_by_id(role.id)
                roles_rep[r] = x.roles[role]
                r._complexes.add(x)
            x.roles = roles_rep

        self.roles += roles_to_add
        self.complexes += complexes

    def add_compounds(self, compounds: list):
        """

        :param compounds:
        :return:
        """
        duplicates = list(filter(lambda x: x.id in self.compounds, compounds))
        if len(duplicates) > 0:
            logger.error("unable to add compounds [%s] already present in the template", duplicates)
            return None

        for x in compounds:
            x._template = self
        self.compounds += compounds

    def add_comp_compounds(self, comp_compounds: list):
        """
        Add a compartment compounds (i.e., species) to the template
        :param comp_compounds:
        :return:
        """
        duplicates = list(filter(lambda x: x.id in self.compcompounds, comp_compounds))
        if len(duplicates) > 0:
            logger.error("unable to add comp compounds [%s] already present in the template", duplicates)
            return None

        for x in comp_compounds:
            x._template = self
            if x.cpd_id in self.compounds:
                x._template_compound = self.compounds.get_by_id(x.cpd_id)
                x._template_compound.species.add(x)
        self.compcompounds += comp_compounds

    def add_reactions(self, reaction_list: list):
        """

        :param reaction_list:
        :return:
        """
        duplicates = list(filter(lambda x: x.id in self.reactions, reaction_list))
        if len(duplicates) > 0:
            logger.error("unable to add reactions [%s] already present in the template", duplicates)
            return None

        for x in reaction_list:
            metabolites_replace = {}
            complex_replace = set()
            x._template = self
            for comp_cpd, coefficient in x.metabolites.items():
                if comp_cpd.id not in self.compcompounds:
                    self.add_comp_compounds([comp_cpd])
                metabolites_replace[self.compcompounds.get_by_id(comp_cpd.id)] = coefficient
            for cpx in x.complexes:
                if cpx.id not in self.complexes:
                    self.add_complexes([cpx])
                complex_replace.add(self.complexes.get_by_id(cpx.id))
            x._metabolites = metabolites_replace
            x.complexes = complex_replace

        self.reactions += reaction_list
        
    def get_role_sources(self):
        pass
    
    def get_complex_sources(self):
        pass
        
    def get_complex_from_role(self, roles):
        cpx_role_str = ';'.join(sorted(roles))
        if cpx_role_str in self.role_set_to_cpx:
            return self.role_set_to_cpx[cpx_role_str]
        return None

    @staticmethod
    def get_last_id_value(object_list, s):
        last_id = 0
        for o in object_list:
            if o.id.startswith(s):
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

    #def _to_object(self, key, data):
    #    if key == 'compounds':
    #        return NewModelTemplateCompound.from_dict(data, self)
    #    if key == 'compcompounds':
    #        return NewModelTemplateCompCompound.from_dict(data, self)
    #    #if key == 'reactions':
    #    #    return NewModelTemplateReaction.from_dict(data, self)
    #    if key == 'roles':
    #        return NewModelTemplateRole.from_dict(data, self)
    #    if key == 'subsystems':
    #        return NewModelTemplateComplex.from_dict(data, self)
    #    return super()._to_object(key, data)

    def get_data(self):
        compartments = []
        return {
            '__VERSION__': self.__VERSION__,
            'id': self.id,
            'name': self.name,
            'domain': self.domain,
            'biochemistry_ref': self.biochemistry_ref,
            'type': 'Test',
            'biomasses': [],
            'compartments': [{'aliases': [],
   'hierarchy': 3,
   'id': 'c',
   'index': '0',
   'name': 'Cytosol',
   'pH': 7},
  {'aliases': [],
   'hierarchy': 0,
   'id': 'e',
   'index': '1',
   'name': 'Extracellular',
   'pH': 7}],
            'compcompounds': list(map(lambda x: x.get_data(), self.compcompounds)),
            'compounds': list(map(lambda x: x.get_data(), self.compounds)),
            'roles': list(map(lambda x: x.get_data(), self.roles)),
            'complexes': list(map(lambda x: x.get_data(), self.complexes)),
            'reactions': list(map(lambda x: x.get_data(), self.reactions)),
            'pathways': [],
            'subsystems': [],
        }

    def _repr_html_(self):
        """
        taken from cobra.core.Model :)
        :return:
        """
        return """
        <table>
            <tr>
                <td><strong>ID</strong></td>
                <td>{id}</td>
            </tr><tr>
                <td><strong>Memory address</strong></td>
                <td>{address}</td>
            </tr><tr>
                <td><strong>Number of metabolites</strong></td>
                <td>{num_metabolites}</td>
            </tr><tr>
                <td><strong>Number of species</strong></td>
                <td>{num_species}</td>
            </tr><tr>
                <td><strong>Number of reactions</strong></td>
                <td>{num_reactions}</td>
            </tr><tr>
                <td><strong>Number of biomasses</strong></td>
                <td>{num_bio}</td>
            </tr><tr>
                <td><strong>Number of roles</strong></td>
                <td>{num_roles}</td>
            </tr><tr>
                <td><strong>Number of complexes</strong></td>
                <td>{num_complexes}</td>
            </tr>
          </table>""".format(
            id=self.id,
            address='0x0%x' % id(self),
            num_metabolites=len(self.compounds),
            num_species=len(self.compcompounds),
            num_reactions=len(self.reactions),
            num_bio=len(self.biomasses),
            num_roles=len(self.roles),
            num_complexes=len(self.complexes))
