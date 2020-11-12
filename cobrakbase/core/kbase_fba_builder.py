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
    def from_cobra(object_id, model, solution, media, ws, target_reaction):
        flux_dist = dict(solution.fluxes)
        b = KBaseFBABuilder(flux_dist)
        b.id = object_id
        b.model = model
        b.media = media
        b.ws = ws
        b.objective_value = solution.fluxes[target_reaction]
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
            "FBABiomassVariables": [],
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
            variable_min = rxn.lower_bound
            variable_max = rxn.upper_bound
            variable_class = 'unknown'
            if varname in self._fva_data:
                variable_min, variable_max = self._fva_data[varname]
                variable_class = self.get_variable_class(variable_min, variable_max)
            variable_data = {
                "class": variable_class,
                "lowerBound": rxn.lower_bound,
                "max": variable_max,
                "min": variable_min,
                "upperBound": rxn.upper_bound, 
                "other_max": [],
                "other_min": [],
                "other_values": [],
                "value": value, # in kbase we assume positive uptake negative excretion
                "variableType": "flux"
            }
            variable_key = "FBAReactionVariables"
            if varname.startswith("EX_"):
                lower = variable_data["lowerBound"]
                variable_data["lowerBound"] = -1*variable_data["upperBound"]
                variable_data["upperBound"] = -1*lower
                lower = variable_data["min"]
                variable_data["min"] = -1*variable_data["max"]
                variable_data["max"] = -1*lower
                variable_data["value"] = -1*variable_data["value"]
                variable_data["variableType"] = "drainflux"
                variable_data["modelcompound_ref"] = "~/fbamodel/modelcompounds/id/"+varname[3:],
                variable_key = "FBACompoundVariables"
            elif varname.endswith("_biomass") or varname.startswith("DM_"):
                variable_data["variableType"] = "biomassflux"
                variable_data["biomass_ref"] = "~/fbamodel/biomasses/id/"+varname[0:-8],                
                variable_key = "FBABiomassVariables"
            else:
                variable_data["modelreaction_ref"] = "~/fbamodel/modelreactions/id/"+varname
                variable_data["exp_state"] = 'unknown'
                variable_data["biomass_dependencies"] = []
                variable_data["coupled_reactions"] = []
                variable_data["expression"] = 0
                variable_data["scaled_exp"] = 0
            fbaobj[variable_key].append(variable_data)
        return fbaobj