import copy
from cobra.core import Model
from cobrakbase.core.kbaseobject import KBaseObject
from cobrakbase.core.kbasebiochem.media import Media
from cobrakbase.core.kbasefba.fbamodel_metabolite import ModelCompound
from cobrakbase.core.kbasefba.fbamodel_reaction import ModelReaction

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

    def __init__(self, compartment_id: str, name: str, ph: float, potential: float, index: int):
        self._model = None
        self.id = compartment_id
        self.name = name
        self.ph = ph
        self.potential = potential
        self.index = index

    @staticmethod
    def from_json(data):
        data_copy = copy.deepcopy(data)
        return ModelCompartment(data_copy['id'], data_copy['label'],
                                data_copy['pH'], data_copy['potential'],
                                data_copy['compartmentIndex'])

    def _to_json(self):
        return {
            'compartment_ref': '~/template/compartments/id/' + self.id[0],  # TODO: resolve from template
            'id': self.id,
            'compartmentIndex': self.index,
            'label': self.name,
            'pH': self.ph,
            'potential': self.potential,
        }


class FBAModel(KBaseObject, Model):

    def __init__(self, data=None, info=None, args=None, kbase_type=None):
        KBaseObject.__init__(self, data, info, args, kbase_type)
        Model.__init__(self, self.data['id'], self.data['name'])
        self._model_compartments = {}

    @staticmethod
    def from_kbase_json(self, data, info=None, args=None):
        model = FBAModel({}, info, args)
        return model

    @Model.compartments.getter
    def compartments(self):
        return {cmp.id: cmp.name for cmp in self._model_compartments}

    def get_exchange_by_metabolite_id(self, metabolite_id):
        return list(filter(lambda x: list(x.metabolites)[0].id == metabolite_id, self.exchanges))

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
        for exchange_reaction in self.exchanges:
            exchange_reaction.lower_bound = 0
        if type(medium) == Media:
            in_model = dict(filter(lambda x: x[0] in self.metabolites, medium.get_media_constraints().items()))
            for compound_id in in_model:
                for exchange_reaction in self.get_exchange_by_metabolite_id(compound_id):
                    exchange_reaction.lower_bound, exchange_reaction.upper_bound = in_model[compound_id]
        else:
            Model.medium.fset(self, medium)

    def _to_json(self):
        from cobrakbase.core.kbasefba.fbamodel_from_cobra import CobraModelConverter
        data = {}
        ignore = {'modelcompounds', 'modelreactions'}
        for key in self.data_keys:
            if key not in ignore:
                if self.data_keys[key] is list:
                    data[key] = list(map(lambda x: x.get_data() if 'get_data' in dir(x) else x, self.data[key]))
                else:
                    data[key] = self.data[key]

        data['modelcompounds'] = []
        for metabolite in self.metabolites:
            if type(metabolite) is ModelCompound:
                data['modelcompounds'].append(metabolite._to_json())
            else:
                data['modelcompounds'].append(ModelCompound.from_cobra_metabolite(metabolite)._to_json())
        for reaction in self.reactions:
            if not CobraModelConverter.reaction_is_drain(reaction) and \
                    not CobraModelConverter.reaction_is_biomass(reaction):
                if type(metabolite) is ModelReaction:
                    data['modelreactions'].append(reaction._to_json())
                else:
                    data['modelreactions'].append(ModelReaction.from_cobra_reaction(reaction)._to_json())

        return data
