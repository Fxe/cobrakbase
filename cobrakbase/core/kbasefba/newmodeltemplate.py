import logging
from cobrakbase.core.kbaseobject import KBaseObject, KBaseObjectBase, AttrDict
from cobrakbase.core.kbasegenomesgenome import normalize_role
from cobra.core.dictlist import DictList
from cobrakbase.kbase_object_info import KBaseObjectInfo
from cobrakbase.core.kbasefba.newmodeltemplate_complex import (
    NewModelTemplateRole,
    NewModelTemplateComplex,
)
from cobrakbase.core.kbasefba.newmodeltemplate_metabolite import (
    NewModelTemplateCompound,
    NewModelTemplateCompCompound,
)
from cobrakbase.core.kbasefba.newmodeltemplate_reaction import NewModelTemplateReaction
from modelseedpy.core.mstemplate import MSTemplate, MSTemplateCompartment

logger = logging.getLogger(__name__)


class TemplateRole(KBaseObjectBase):
    def __init__(self, data, template=None):
        super().__init__(data)
        self.template = template


class TemplateCompartment(MSTemplateCompartment):
    def __init__(
        self, compartment_id: str, name: str, ph: float, hierarchy=0, aliases=None
    ):
        super().__init__(compartment_id, name, ph, hierarchy, aliases)


class NewModelTemplate(MSTemplate):
    def __init__(
        self,
        template_id,
        name="",
        domain="",
        template_type="",
        version=1,
        info=None,
        args=None,
    ):
        super().__init__(template_id, name, domain, template_type, version)
        self.__VERSION__ = version
        self.biochemistry_ref = ""
        self.info = (
            info if info else KBaseObjectInfo(object_type="KBaseFBA.NewModelTemplate")
        )
        self.args = args

    def get_role_sources(self):
        pass

    def get_complex_sources(self):
        pass

    @staticmethod
    def get_last_id_value(object_list, s):
        last_id = 0
        for o in object_list:
            if o.id.startswith(s):
                number_part = id[len(s) :]
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

    def get_data(self):
        d = {
            "__VERSION__": self.__VERSION__,
            "id": self.id,
            "name": self.name,
            "domain": self.domain,
            "biochemistry_ref": self.biochemistry_ref,
            "type": "Test",
            "compartments": list(map(lambda x: x.get_data(), self.compartments)),
            "compcompounds": list(map(lambda x: x.get_data(), self.compcompounds)),
            "compounds": list(map(lambda x: x.get_data(), self.compounds)),
            "roles": list(map(lambda x: x.get_data(), self.roles)),
            "complexes": list(map(lambda x: x.get_data(), self.complexes)),
            "reactions": list(map(lambda x: x.get_data(), self.reactions)),
            "biomasses": list(map(lambda x: x.get_data(), self.biomasses)),
            "pathways": [],
            "subsystems": [],
        }
        if self.drains is not None:
            d["drain_list"] = {c.id: t for c, t in self.drains.items()}

        return d

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
            address="0x0%x" % id(self),
            num_metabolites=len(self.compounds),
            num_species=len(self.compcompounds),
            num_reactions=len(self.reactions),
            num_bio=len(self.biomasses),
            num_roles=len(self.roles),
            num_complexes=len(self.complexes),
        )
