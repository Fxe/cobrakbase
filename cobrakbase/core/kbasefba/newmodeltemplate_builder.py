import logging
from copy import deepcopy
from cobrakbase.core.kbasefba.newmodeltemplate import (
    NewModelTemplate,
    TemplateCompartment,
)
from cobrakbase.core.kbasefba.newmodeltemplate_complex import (
    NewModelTemplateRole,
    NewModelTemplateComplex,
)
from cobrakbase.core.kbasefba.newmodeltemplate_metabolite import (
    NewModelTemplateCompound,
    NewModelTemplateCompCompound,
)
from cobrakbase.core.kbasefba.newmodeltemplate_reaction import NewModelTemplateReaction
from cobrakbase.kbase_object_info import KBaseObjectInfo
from cobrakbase.core.kbaseobject import AttrDict
from modelseedpy.core.mstemplate import MSTemplateBuilder

logger = logging.getLogger(__name__)


class NewModelTemplateBuilder(MSTemplateBuilder):
    def __init__(
        self,
        template_id,
        name="",
        domain="",
        template_type="",
        version=1,
        info=None,
        biochemistry=None,
        biomasses=None,
        pathways=None,
        subsystems=None,
    ):
        self.info = info
        self.biochemistry_ref = None
        super().__init__(
            template_id,
            name,
            domain,
            template_type,
            version,
            info,
            biochemistry,
            biomasses,
            pathways,
            subsystems,
        )

    @staticmethod
    def from_dict(d, info=None, args=None):
        """

        :param d:
        :param info:
        :param args:
        :return:
        """
        version = d["__VERSION__"] if "__VERSION__" in d else None
        builder = NewModelTemplateBuilder(
            d["id"], d["name"], d["domain"], d["type"], version, info
        )
        builder.compartments = d["compartments"]
        builder.roles = d["roles"]
        builder.complexes = d["complexes"]
        builder.compounds = d["compounds"]
        builder.compartment_compounds = d["compcompounds"]
        builder.reactions = d["reactions"]
        builder.biochemistry_ref = d["biochemistry_ref"]
        builder.biomasses = d["biomasses"]
        if 'drain_list' in d:
            builder.drains = d['drain_list']

        return builder

    @staticmethod
    def from_template(template):
        b = NewModelTemplateBuilder()
        for o in template.compartments:
            b.compartments.append(deepcopy(o))

        return b

    def build(self):
        template = NewModelTemplate(
            self.id, self.name, self.domain, self.template_type, self.version
        )
        template.add_compartments(
            list(map(lambda x: TemplateCompartment.from_dict(x), self.compartments))
        )
        template.biochemistry_ref = self.biochemistry_ref  # FIXME: change to ObjectInfo
        template.info = (
            self.info
            if self.info
            else KBaseObjectInfo(object_type="KBaseFBA.NewModelTemplate")
        )
        template.add_compounds(
            list(map(lambda x: NewModelTemplateCompound.from_dict(x), self.compounds))
        )
        template.add_comp_compounds(
            list(
                map(
                    lambda x: NewModelTemplateCompCompound.from_dict(x),
                    self.compartment_compounds,
                )
            )
        )
        template.add_roles(
            list(map(lambda x: NewModelTemplateRole.from_dict(x), self.roles))
        )
        template.add_complexes(
            list(
                map(
                    lambda x: NewModelTemplateComplex.from_dict(x, template),
                    self.complexes,
                )
            )
        )
        template.add_reactions(
            list(
                map(
                    lambda x: NewModelTemplateReaction.from_dict(x, template),
                    self.reactions,
                )
            )
        )
        template.biomasses += list(
            map(lambda x: AttrDict(x), self.biomasses)
        )  # TODO: biomass object

        for compound_id, (lb, ub) in self.drains.items():
            template.add_drain(compound_id, lb, ub)

        return template
