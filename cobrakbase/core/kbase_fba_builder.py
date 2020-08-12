import logging

logger = logging.getLogger(__name__)


class KBaseFBABuilder:
    
    def __init__(self, flux_dist):
        self.flux_dist = flux_dist
        self.id = 'fba1'
        self.model = None
        self.media = None
        self.objective_value = None
        self.ws = None
        self._fva_data = {}
    
    @staticmethod
    def from_cobra(object_id, model, solution, media, ws):
        flux_dist = dict(solution.fluxes)
        b = KBaseFBABuilder(flux_dist)
        b.id = object_id
        b.model = model
        b.media = media
        b.ws = ws
        b.objective_value = solution.objective_value
        return b
    
    def with_cobra_fva_solution(self, cobra_fva_result):
        for rxn_id, d in cobra_fva_result.iterrows():
            self._fva_data[rxn_id] = (d['minimum'], d['maximum'])
        return self
    
    @property
    def fbamodel_ref(self):
        #65434/6/1 filipeliu:narrative_1592958114519/model1
        return "{}/{}".format(self.ws, self.model.id)
    
    @property
    def media_ref(self):
        #65434/5/1 filipeliu:narrative_1592958114519/Carbon-D-Glucose
        return "{}/{}".format(self.ws, self.media.data['name'])

    @staticmethod
    def get_variable_class(variable_min, variable_max):
        variable_class = 'unknown'
        if variable_min is None or variable_max is None:
            return variable_class
        if variable_min == 0 and variable_max == 0:
            variable_class = 'Blocked'
        elif variable_min > 0 and variable_max > 0:
            variable_class = 'Positive'
        elif variable_min >= 0 and variable_max > 0:
            variable_class = 'Positive variable'
        elif variable_min < 0 and variable_max < 0:
            variable_class = 'Negative'
        elif variable_min < 0 and variable_max <= 0:
            variable_class = 'Negative variable'
        else:
            variable_class = 'Variable'
        return variable_class

    def build(self):
        # Saving final solution as an FBA object in KBase
        fbaobj = {
            "FBABiomassVariables": [
                {
                    "biomass_ref": "~/fbamodel/biomasses/id/bio1",
                    "class": "unknown",
                    "lowerBound": self.model.reactions.bio1_biomass.lower_bound,
                    "upperBound": self.model.reactions.bio1_biomass.upper_bound,
                    "max": self.model.reactions.bio1_biomass.upper_bound,
                    "min": self.model.reactions.bio1_biomass.lower_bound,
                    "other_max": [],
                    "other_min": [],
                    "other_values": [],
                    "value": self.flux_dist['bio1_biomass'],
                    "variableType": "biomassflux"
                }
            ],
            "FBACompoundBounds": [],
            "FBACompoundVariables": [],
            "FBAConstraints": [],
            "FBADeletionResults": [],
            "FBAMetaboliteProductionResults": [],
            "FBAMinimalMediaResults": [],
            "FBAMinimalReactionsResults": [],
            "FBAPromResults": [],
            "FBAReactionBounds": [],
            "FBAReactionVariables": [],
            "FBATintleResults": [],
            "MFALog": "",
            "PROMKappa": 1,
            "QuantitativeOptimizationSolutions": [],
            "__VERSION__": 1,
            "additionalCpd_refs": [],
            "allReversible": 0,
            "biomassRemovals": {},
            "biomassflux_objterms": {
                "bio1": 1
            },
            "calculateReactionKnockoutSensitivity": 0,
            "comboDeletions": 0,
            "compoundflux_objterms": {},
            "decomposeReversibleDrainFlux": 0,
            "decomposeReversibleFlux": 0,
            "defaultMaxDrainFlux": 0,
            "defaultMaxFlux": 1000,
            "defaultMinDrainFlux": -1000,
            "drainfluxUseVariables": 0,
            "fbamodel_ref": self.fbamodel_ref,
            "findMinimalMedia": 0,
            "fluxMinimization": 1,
            "fluxUseVariables": 0,
            "fva": 0,
            "gapfillingSolutions": [],
            "geneKO_refs": [],
            "id": self.id,
            "inputfiles": {},
            "maximizeActiveReactions": 0,
            "maximizeObjective": 1,
            "media_list_refs": [],
            "media_ref": self.media_ref,
            "minimizeErrorThermodynamicConstraints": 0,
            "minimize_reaction_costs": {},
            "minimize_reactions": 0,
            "noErrorThermodynamicConstraints": 0,
            "numberOfSolutions": 1,
            "objectiveConstraintFraction": 0.1,
            "objectiveValue": self.objective_value,
            "other_objectives": [],
            "outputfiles": {},
            "parameters": {
                "Auxotrophy metabolite list": "",
                "Beachhead metabolite list": "",
                "minimum_target_flux": "0.01",
                "save phenotype fluxes": "0",
                "suboptimal solutions": "1"
            },
            "quantitativeOptimization": 0,
            "reactionKO_refs": [],
            "reactionflux_objterms": {},
            "simpleThermoConstraints": 0,
            "thermodynamicConstraints": 0,
            "uptakeLimits": {}
        }
        
        for varname, value in self.flux_dist.items():
            rxn = self.model.reactions.get_by_id(varname)

            if varname.startswith("EX_"):
                variable_min = rxn.lower_bound
                variable_max = rxn.upper_bound
                variable_class = 'unknown'
                if varname in self._fva_data:
                    variable_min, variable_max = self._fva_data[varname]
                    variable_class = self.get_variable_class(variable_min, variable_max)
                fbaobj["FBACompoundVariables"].append({
                    "class": variable_class,
                    "lowerBound": -1 * rxn.upper_bound,
                    "max": -1 * variable_min,
                    "min": -1 * variable_max,
                    "upperBound": -1 * rxn.lower_bound,
                    "modelcompound_ref": "~/fbamodel/modelcompounds/id/"+varname[3:],
                    "other_max": [],
                    "other_min": [],
                    "other_values": [],
                    "value": -1*value, # in kbase we assume positive uptake negative excretion
                    "variableType": "drainflux"
                })
            elif varname.endswith("_biomass") or varname.startswith("DM_"):
                logger.debug("SKIP %s", varname)
            else:
                variable_min = rxn.lower_bound
                variable_max = rxn.upper_bound
                variable_class = 'unknown'
                if varname in self._fva_data:
                    variable_min, variable_max = self._fva_data[varname]
                    variable_class = self.get_variable_class(variable_min, variable_max)

                fbaobj["FBAReactionVariables"].append({
                    "biomass_dependencies": [],
                    "class": variable_class,
                    "coupled_reactions": [],
                    "exp_state": 'unknown',  # usage ?
                    "expression": 0,
                    "min": variable_min,
                    "max": variable_max,
                    "lowerBound": rxn.lower_bound,
                    "upperBound": rxn.upper_bound,
                    "modelreaction_ref": "~/fbamodel/modelreactions/id/"+varname,
                    "other_max": [],
                    "other_min": [],
                    "other_values": [],
                    "scaled_exp": 0,  # what is this ?
                    "value": value,
                    "variableType": "flux"  # what is this ?
                })
        return fbaobj