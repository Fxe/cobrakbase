import logging
import json
import copy
from typing import Union, Optional
from cobra.core import Model, Reaction
from cobrakbase.kbase_object_info import KBaseObjectInfo
from cobrakbase.core.kbaseobject import KBaseObject
from cobrakbase.core.kbasebiochem.media import Media
from cobrakbase.core.kbasefba.fbamodel_metabolite import ModelCompound
from cobrakbase.core.kbasefba.fbamodel_reaction import ModelReaction
from cobrakbase.core.kbasefba.fbamodel_biomass import Biomass

logger = logging.getLogger(__name__)


class ModelCompartment:
    """
    typedef structure {
        modelcompartment_id id;
        compartment_ref compartment_ref;
        int compartmentIndex;
        string label;
        float pH;
        float potential;
    } ModelCompartment;
    """

    def __init__(
        self, compartment_id: str, name: str, ph: float, potential: float, index: int
    ):
        self._model = None
        self.id = compartment_id
        self.name = name
        self.ph = ph
        self.potential = potential
        self.index = index

    @staticmethod
    def from_json(data):
        data_copy = copy.deepcopy(data)
        return ModelCompartment(
            data_copy["id"],
            data_copy["label"],
            data_copy["pH"],
            data_copy["potential"],
            data_copy["compartmentIndex"],
        )

    def get_sbml_notes_key(self):
        return f"kbase_compartment_data_{self.id}"

    def get_sbml_notes_data(self):
        return {
            "compartmentIndex": self.index,
            "pH": self.ph,
            "potential": self.potential,
        }

    def _to_json(self):
        return {
            "compartment_ref": f"~/template/compartments/id/{self.id[0]}",  # TODO: resolve from template
            "id": self.id,
            "compartmentIndex": self.index,
            "label": self.name,
            "pH": self.ph,
            "potential": self.potential,
        }


class FBAModel(KBaseObject, Model):
    """
        fbamodel_id id; id_or_model

    string name; name
          string source;
      source_id source_id;
    string type;
    template_ref template_ref;

    list<ModelGapfill> gapfillings;
    list<ModelGapgen> gapgens;
    list<Biomass> biomasses;
    list<ModelCompartment> modelcompartments;
    list<ModelCompound> modelcompounds;
    list<ModelReaction> modelreactions;

          @optional
          list<genome_ref> other_genome_refs;
          ComputedAttributes attributes;
          list<ModelReaction> abstractreactions;
          list<ModelReaction> gapfilledcandidates;
          metagenome_ref metagenome_ref;
          genome_ref genome_ref;
          list<template_ref> template_refs;
          float ATPSynthaseStoichiometry;
          float ATPMaintenance;
          list<ModelQuantOpt> quantopts;
    """

    OBJECT_TYPE = "KBaseFBA.FBAModel"

    SBML_FIELD_SOURCE = "kbase_source"
    SBML_FIELD_SOURCE_ID = "kbase_source_id"
    SBML_FIELD_GAPFILLINGS = "kbase_gapfillings"
    SBML_FIELD_MODEL_TYPE = "kbase_model_type"
    SBML_FIELD_GAPGENS = "kbase_gapgens"
    SBML_FIELD_TEMPLATE_REFS = "kbase_template_refs"
    SBML_FIELD_GENOME_REFS = "kbase_genome_ref"
    SBML_FIELD_ATTRIBUTES = "kbase_attributes"

    def _get_gapfillings(self):
        if self.SBML_FIELD_GAPFILLINGS in self.notes:
            return json.loads(
                self.notes[self.SBML_FIELD_GAPFILLINGS].replace("&quot;", '"')
            )
        else:
            return []

    def _set_gapfillings(self, value: list):
        self.notes[self.SBML_FIELD_GAPFILLINGS] = json.dumps(value)

    gapfillings = property(_get_gapfillings, _set_gapfillings)

    def _get_computed_attributes(self):
        if self.SBML_FIELD_ATTRIBUTES in self.notes:
            return json.loads(
                self.notes[self.SBML_FIELD_ATTRIBUTES].replace("&quot;", '"')
            )
        else:
            return None

    def _set_computed_attributes(self, value: dict):
        self.notes[self.SBML_FIELD_ATTRIBUTES] = json.dumps(value)

    computed_attributes = property(_get_computed_attributes, _set_computed_attributes)

    def _get_source(self):
        if self.SBML_FIELD_SOURCE in self.notes:
            return self.notes[self.SBML_FIELD_SOURCE]
        else:
            return ""

    def _set_source(self, value: str):
        self.notes[self.SBML_FIELD_SOURCE] = value

    source = property(_get_source, _set_source)

    def _get_source_id(self):
        if self.SBML_FIELD_SOURCE_ID in self.notes:
            return self.notes[self.SBML_FIELD_SOURCE_ID]
        else:
            return ""

    def _set_source_id(self, value: str):
        self.notes[self.SBML_FIELD_SOURCE_ID] = value

    source_id = property(_get_source_id, _set_source_id)

    def _get_type(self):
        if self.SBML_FIELD_MODEL_TYPE in self.notes:
            return self.notes[self.SBML_FIELD_MODEL_TYPE]
        else:
            return ""

    def _set_type(self, value: str):
        self.notes[self.SBML_FIELD_MODEL_TYPE] = value

    model_type = property(_get_type, _set_type)

    def _get_genome_ref(self):
        if self.SBML_FIELD_GENOME_REFS in self.notes:
            return self.notes[self.SBML_FIELD_GENOME_REFS]
        else:
            return None

    def _set_genome_ref(self, value: str):
        self.notes[self.SBML_FIELD_GENOME_REFS] = value

    genome_ref = property(_get_genome_ref, _set_genome_ref)

    def _get_template_ref(self):
        if self.SBML_FIELD_TEMPLATE_REFS in self.notes:
            return self.notes[self.SBML_FIELD_TEMPLATE_REFS]
        else:
            return None

    def _set_template_ref(self, value: str):
        self.notes[self.SBML_FIELD_TEMPLATE_REFS] = value

    template_ref = property(_get_template_ref, _set_template_ref)

    def _get_gapgens(self):
        if self.SBML_FIELD_GAPGENS in self.notes:
            return json.loads(
                self.notes[self.SBML_FIELD_GAPGENS].replace("&quot;", '"')
            )
        else:
            return []

    def _set_gapgens(self, value):
        self.notes[self.SBML_FIELD_GAPGENS] = json.dumps(value)

    gapgens = property(_get_gapgens, _set_gapgens)

    def future__init__(
        self,
        id_or_model: Union[str, "Model", None] = None,
        name: Optional[str] = None,
        info=None,
        args=None,
    ) -> None:
        """

        @param id_or_model:
        @param name:
        @param info:
        @param args:
        @return:
        """
        if info is None:
            info = KBaseObjectInfo(object_type=FBAModel.OBJECT_TYPE)
        KBaseObject.__init__(self, {}, info, args, None)
        Model.__init__(self, id_or_model, name)
        self.source = None
        self.source_id = None
        self.type = None
        self.template = None
        self.gap_fillings = None
        self.gap_gens = None

    def __init__(self, data=None, info=None, args=None, kbase_type=None):
        if info is None:
            info = KBaseObjectInfo(object_type=FBAModel.OBJECT_TYPE)
        KBaseObject.__init__(self, data, info, args, kbase_type)
        Model.__init__(self, self.data["id"], self.data["name"])
        self._model_compartments = {}

    @staticmethod
    def from_kbase_json(self, data, info=None, args=None):
        model = FBAModel({}, info, args)
        return model

    @staticmethod
    def from_kbase_json(self, data, info=None, args=None):
        model = FBAModel({}, info, args)
        return model

    @Model.compartments.getter
    def compartments(self):
        return {cmp.id: cmp.name for (k, cmp) in self._model_compartments.items()}

    @compartments.setter
    def compartments(self, value: dict) -> None:
        if value is None:
            raise ValueError("value cannot be None")
        for k in value:
            v = value[k]
            if v is None or (type(v) != str and not isinstance(v, ModelCompartment)):
                raise ValueError(
                    f"value for compartment must be either string or ModelCompartment, found {type(v)}"
                )
            if type(v) == str:
                self._model_compartments[k] = ModelCompartment(k, v, 7.0, 0.0, 0)
            else:
                self._model_compartments[v.id] = v
        self._compartments.update(value)

    def get_exchange_by_metabolite_id(self, metabolite_id):
        return list(
            filter(lambda x: list(x.metabolites)[0].id == metabolite_id, self.exchanges)
        )

    @Model.medium.setter
    def medium(self, medium):
        """Get or set the constraints on the model exchanges.

        `model.medium` returns a dictionary of the bounds for each of the
        boundary reactions, in the form of `{rxn_id: bound}`, where `bound`
        specifies the absolute value of the bound in direction of metabolite
        creation (i.e., lower_bound for `met <--`, upper_bound for `met -->`)

        Parameters
        ----------
        medium: dictionary-like
            The medium to initialize. medium should be a dictionary defining
            `{rxn_id: bound}` pairs.

            or

            KBase Media object enconding medium
        """
        if type(medium) == Media:
            for exchange_reaction in self.exchanges:
                if exchange_reaction.upper_bound < 0:
                    exchange_reaction.upper_bound = 0
                exchange_reaction.lower_bound = 0
            in_model = dict(
                filter(
                    lambda x: x[0] in self.metabolites,
                    medium.get_media_constraints().items(),
                )
            )
            for compound_id in in_model:
                for exchange_reaction in self.get_exchange_by_metabolite_id(
                    compound_id
                ):
                    (
                        exchange_reaction.lower_bound,
                        exchange_reaction.upper_bound,
                    ) = in_model[compound_id]
        else:
            Model.medium.fset(self, medium)

    def _to_json(self):
        from cobrakbase.core.kbasefba.fbamodel_from_cobra import CobraModelConverter

        data = {}
        ignore = {"modelcompounds", "modelreactions", "biomasses", "modelcompartments"}

        data["modelcompartments"] = []
        for cmp_id, name in self.compartments.items():
            model_compartment = {
                "id": cmp_id,
                "label": name,
                "compartment_ref": "~/template/compartments/id/" + cmp_id[:-1],
            }
            cmp_meta_data_key = f"kbase_compartment_data_{cmp_id}"
            if cmp_meta_data_key in self.notes:
                m = self.notes[cmp_meta_data_key]
                if type(m) == str:
                    extra_data = json.loads(m.replace("&apos;", '"'))
                elif type(m) == dict:
                    extra_data = m
                else:
                    raise ValueError(
                        f"note field for {cmp_meta_data_key} must be either str or dict, found: {type(m)}"
                    )
                if "compartmentIndex" in extra_data:
                    extra_data["compartmentIndex"] = int(extra_data["compartmentIndex"])
                if "pH" in extra_data:
                    extra_data["pH"] = float(extra_data["pH"])
                if "potential" in extra_data:
                    extra_data["potential"] = float(extra_data["potential"])
                model_compartment.update(extra_data)
            data["modelcompartments"].append(model_compartment)

        for key in self.data_keys:
            if key not in ignore:
                if self.data_keys[key] is list:
                    data[key] = list(
                        map(
                            lambda x: x.get_data() if "get_data" in dir(x) else x,
                            self.data[key],
                        )
                    )
                else:
                    data[key] = self.data[key]

        if "kbase_template_refs" in self.notes:
            template_refs = self.notes["kbase_template_refs"].split(";")
            data["template_refs"] = template_refs
            data["template_ref"] = template_refs[0]

        data["modelcompounds"] = []
        data["modelreactions"] = []
        data["biomasses"] = []

        computed_attributes = self.computed_attributes
        if computed_attributes:
            data["attributes"] = computed_attributes
        data["genome_ref"] = self.genome_ref
        data["source_id"] = self.source_id
        data["source"] = self.source
        data["type"] = self.model_type
        data["gapgens"] = self.gapgens
        data["gapfillings"] = self.gapfillings
        data["drain_list"] = {}

        for metabolite in self.metabolites:
            if type(metabolite) is ModelCompound:
                data["modelcompounds"].append(metabolite._to_json())
            else:
                data["modelcompounds"].append(
                    ModelCompound.from_cobra_metabolite(metabolite)._to_json()
                )

        for reaction in self.reactions:
            if CobraModelConverter.reaction_is_biomass(reaction):
                if type(reaction) is Biomass:
                    data["biomasses"].append(reaction._to_json())
                elif type(reaction) is Reaction:
                    data["biomasses"].append(
                        CobraModelConverter.convert_reaction_to_biomass(
                            reaction
                        )._to_json()
                    )
                else:
                    logger.warning(f"unable to biomass type {type(reaction)}")
            elif CobraModelConverter.reaction_is_drain(
                reaction
            ) and not CobraModelConverter.reaction_is_exchange(reaction):
                cpd_id = list(reaction.metabolites)[0].id
                if cpd_id not in data["drain_list"]:
                    data["drain_list"][cpd_id] = [0, 0]
                if reaction.lower_bound < 0:
                    data["drain_list"][cpd_id][0] = reaction.lower_bound
                if reaction.upper_bound > 0:
                    data["drain_list"][cpd_id][1] = reaction.upper_bound
            elif not CobraModelConverter.reaction_is_exchange(reaction):
                if type(reaction) is ModelReaction:
                    data["modelreactions"].append(reaction._to_json())
                else:
                    r = ModelReaction.from_cobra_reaction(reaction)
                    r.add_metabolites(reaction.metabolites)
                    r.annotation = reaction.annotation
                    r.notes = reaction.notes
                    r._model = self
                    data["modelreactions"].append(r._to_json())

        return data

    def copy(self):
        from cobrakbase.core.kbasefba.fbamodel_builder import FBAModelBuilder
        from cobrakbase.kbase_object_info import KBaseObjectInfo

        # copy data, info, args
        json = self._to_json()
        info = KBaseObjectInfo.from_kbase_json(self.info.to_kbase_json())
        args = self.get_kbase_args()
        builder = FBAModelBuilder.from_kbase_json(json, info, args)
        
        for r in self.reactions:
            if r.annotation.get('sbo') == 'SBO:0000632':
                builder.with_sink(list(r.metabolites)[0].id, 1000)
            elif r.annotation.get('sbo') == 'SBO:0000628':
                builder.with_demand(list(r.metabolites)[0].id, -1000)             
        
        model_copy = builder.build()
        model_copy.medium = self.medium
        return model_copy
