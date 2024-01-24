from cobra.core.solution import Solution
from cobra.core import Model

# TODO: WORK IN PROGRESS !!

class FBA(Solution):
    """
    /*
FBA object holds the formulation and results of a flux balance analysis study

@optional media_list_refs MFALog maximizeActiveReactions 
@optional calculateReactionKnockoutSensitivity biomassRemovals ExpressionKappa ExpressionOmega 
@optional ExpressionAlpha expression_matrix_ref expression_matrix_column jobnode gapfillingSolutions 
@optional QuantitativeOptimizationSolutions quantitativeOptimization minimize_reactions 
@optional minimize_reaction_costs FBATintleResults FBAMinimalReactionsResults PROMKappa 
@optional phenotypesimulationset_ref objectiveValue phenotypeset_ref promconstraint_ref 
@optional regulome_ref tintleW tintleKappa massbalance rxnprob_ref

@metadata ws maximizeObjective as Maximized
    @metadata ws comboDeletions as Combination deletions
    @metadata ws minimize_reactions as Minimize reactions
    @metadata ws regulome_ref as Regulome
    @metadata ws fbamodel_ref as Model
    @metadata ws promconstraint_ref as PromConstraint
    @metadata ws media_ref as Media
    @metadata ws objectiveValue as Objective
    @metadata ws expression_matrix_ref as ExpressionMatrix
    @metadata ws expression_matrix_column as ExpressionMatrixColumn
    @metadata ws length(biomassflux_objterms) as Number biomass objectives
    @metadata ws length(geneKO_refs) as Number gene KO
    @metadata ws length(reactionKO_refs) as Number reaction KO
    @metadata ws length(additionalCpd_refs) as Number additional compounds
    @metadata ws length(FBAConstraints) as Number constraints
    @metadata ws length(FBAReactionBounds) as Number reaction bounds
    @metadata ws length(FBACompoundBounds) as Number compound bounds
    @metadata ws length(FBACompoundVariables) as Number compound variables
    @metadata ws length(FBAReactionVariables) as Number reaction variables
*/
typedef structure {
  fba_id id;
  bool fva;
  bool fluxMinimization;
  bool findMinimalMedia;
  bool allReversible;
  bool simpleThermoConstraints;
  bool thermodynamicConstraints;
  bool noErrorThermodynamicConstraints;
  bool minimizeErrorThermodynamicConstraints;
  bool quantitativeOptimization;
  bool maximizeObjective;
  mapping<modelcompound_id, float> compoundflux_objterms;
  mapping<modelreaction_id, float> reactionflux_objterms;
  mapping<biomass_id, float> biomassflux_objterms;
  int comboDeletions;
  int numberOfSolutions;
  float objectiveConstraintFraction;
  float defaultMaxFlux;
  float defaultMaxDrainFlux;
  float defaultMinDrainFlux;
  float PROMKappa;
  float tintleW;
  float tintleKappa;
  float ExpressionAlpha;
  float ExpressionOmega;
  float ExpressionKappa;
  bool decomposeReversibleFlux;
  bool decomposeReversibleDrainFlux;
  bool fluxUseVariables;
  bool drainfluxUseVariables;
  bool minimize_reactions;
  bool calculateReactionKnockoutSensitivity;
  bool maximizeActiveReactions;
  string jobnode;
  regulome_ref regulome_ref;
  fbamodel_ref fbamodel_ref;
  rxnprob_ref rxnprob_ref;
  promconstraint_ref promconstraint_ref;
  expression_matrix_ref expression_matrix_ref;
  string expression_matrix_column;
  media_ref media_ref;
  list<media_ref> media_list_refs;
  phenotypeset_ref phenotypeset_ref;
  list<feature_ref> geneKO_refs;
  list<modelreaction_ref> reactionKO_refs;
  list<modelcompound_ref> additionalCpd_refs;
  mapping<string, float> uptakeLimits;
  mapping<modelreaction_id, float> minimize_reaction_costs;
  string massbalance;
  mapping<string, string> parameters;
  mapping<string, list<string>> inputfiles;
  list<FBAConstraint> FBAConstraints;
  list<FBAReactionBound> FBAReactionBounds;
  list<FBACompoundBound> FBACompoundBounds;
  float objectiveValue;
  list<float> other_objectives; @optional
  mediaset_ref mediaset_ref; @optional
  mapping<string, list<string>> outputfiles;
  string MFALog;
  phenotypesimulationset_ref phenotypesimulationset_ref;
  mapping<string, list<string>> biomassRemovals;
  list<FBACompoundVariable> FBACompoundVariables;
  list<FBAReactionVariable> FBAReactionVariables;
  list<FBABiomassVariable> FBABiomassVariables;
  list<FBAPromResult> FBAPromResults;
  list<FBATintleResult> FBATintleResults;
  list<FBADeletionResult> FBADeletionResults;
  list<FBAMinimalMediaResult> FBAMinimalMediaResults;
  list<FBAMetaboliteProductionResult> FBAMetaboliteProductionResults;
  list<FBAMinimalReactionsResult> FBAMinimalReactionsResults;
  list<QuantitativeOptimizationSolution> QuantitativeOptimizationSolutions;
  list<GapfillingSolution> gapfillingSolutions;
} FBA;
    """
    def __init__(self, id:str, model:Model, fva:bool, maximizeObjective:bool):
        pass

    @staticmethod
    def from_kbase_json(d):
        pass

    def aaa(self):
        """
@optional biomass_dependencies coupled_reactions exp_state expression scaled_exp other_values other_max other_min
*/
typedef structure {
  string variableType;
  string class;
  string exp_state;
  float expression;
  float scaled_exp;
  list<tuple<string, string>> biomass_dependencies;
  list<string> coupled_reactions;
  list<float> other_values;
  list<float> other_max;
  list<float> other_min;
} FBAReactionVariable;
        """
        reaction_variable = {
            'modelreaction_ref': '',
            'upperBound': 0.0,  # float
            'lowerBound': 0.0,  # float
            'min': 0.0,  # float
            'max': 0.0,  # float
            'value': 0.0,  # float
        }
        pass

    def to_kbase_json(self):
        data = {
            'fbamodel_ref': str(model.info)
        }


"""
/*
KBase FBA ID
@id kb
*/
typedef string fba_id;

typedef int bool;

/*
Model compound ID
@id external
*/
typedef string modelcompound_id;

/*
Model reaction ID
@id external
*/
typedef string modelreaction_id;

/*
Biomass reaction ID
@id external
*/
typedef string biomass_id;

/*
Reference to regulome
@id ws KBaseRegulation.Regulome
*/
typedef string regulome_ref;

/*
Reference to metabolic model
@id ws KBaseFBA.FBAModel
*/
typedef string fbamodel_ref;

/*
Reference to a model template
@id ws KBaseFBA.ReactionProbabilities
*/
typedef string rxnprob_ref;

/*
Reference to PROM constraints
@id ws KBaseFBA.PromConstraint
*/
typedef string promconstraint_ref;

/*
Reference to expression data
@id ws KBaseFeatureValues.ExpressionMatrix
*/
typedef string expression_matrix_ref;

/*
Reference to a model template
@id ws KBaseBiochem.Media
*/
typedef string media_ref;

/*
Reference to a model template
@id ws KBaseBiochem.MediaSet
*/
typedef string mediaset_ref;

/*
Reference to a phenotype set object
@id ws KBasePhenotypes.PhenotypeSet
*/
typedef string phenotypeset_ref;

/*
Reference to a feature of a genome object
@id subws KBaseGenomes.Genome.features.[*].id
*/
typedef string feature_ref;

/*
Reference to a reaction object in a model
@id subws KBaseFBA.FBAModel.modelreactions.[*].id
*/
typedef string modelreaction_ref;

/*
Reference to a compound object in a model
@id subws KBaseFBA.FBAModel.modelcompounds.[*].id
*/
typedef string modelcompound_ref;

/*
FBAConstraint object
*/
typedef structure {
  string name;
  float rhs;
  string sign;
  mapping<modelcompound_id, float> compound_terms;
  mapping<modelreaction_id, float> reaction_terms;
  mapping<biomass_id, float> biomass_terms;
} FBAConstraint;

/*
FBAReactionBound object
*/
typedef structure {
  modelreaction_ref modelreaction_ref;
  string variableType;
  float upperBound;
  float lowerBound;
} FBAReactionBound;

/*
FBACompoundBound object
*/
typedef structure {
  modelcompound_ref modelcompound_ref;
  string variableType;
  float upperBound;
  float lowerBound;
} FBACompoundBound;

/*
Reference to a phenotype simulation set object
@id ws KBasePhenotypes.PhenotypeSimulationSet
*/
typedef string phenotypesimulationset_ref;

/*
FBACompoundVariable object

@optional other_values other_max other_min
*/
typedef structure {
  modelcompound_ref modelcompound_ref;
  string variableType;
  float upperBound;
  float lowerBound;
  string class;
  float min;
  float max;
  float value;
  list<float> other_values;
  list<float> other_max;
  list<float> other_min;
} FBACompoundVariable;

/*
FBAReactionVariable object



/*
Reference to a biomass object in a model
@id subws KBaseFBA.FBAModel.biomasses.[*].id
*/
typedef string biomass_ref;

/*
FBABiomassVariable object

@optional other_values other_max other_min
*/
typedef structure {
  biomass_ref biomass_ref;
  string variableType;
  float upperBound;
  float lowerBound;
  string class;
  float min;
  float max;
  float value;
  list<float> other_values;
  list<float> other_max;
  list<float> other_min;
} FBABiomassVariable;

/*
FBAPromResult object
*/
typedef structure {
  float objectFraction;
  float alpha;
  float beta;
} FBAPromResult;

/*
Either of two values: 
 - InactiveOn: specified as on, but turns out as inactive
 - ActiveOff: specified as off, but turns out as active
*/
typedef string conflict_state;

/*
Genome feature ID
@id external
*/
typedef string feature_id;

/*
FBATintleResult object
*/
typedef structure {
  float originalGrowth;
  float growth;
  float originalObjective;
  float objective;
  mapping<conflict_state, feature_id> conflicts;
} FBATintleResult;

/*
FBADeletionResult object
*/
typedef structure {
  list<feature_ref> feature_refs;
  float growthFraction;
} FBADeletionResult;

/*
Reference to a compound object
@id subws KBaseBiochem.Biochemistry.compounds.[*].id
*/
typedef string compound_ref;

/*
FBAMinimalMediaResult object
*/
typedef structure {
  list<compound_ref> essentialNutrient_refs;
  list<compound_ref> optionalNutrient_refs;
} FBAMinimalMediaResult;

/*
FBAMetaboliteProductionResult object
*/
typedef structure {
  modelcompound_ref modelcompound_ref;
  float maximumProduction;
} FBAMetaboliteProductionResult;

/*
FBAMinimalReactionsResult object
*/
typedef structure {
  string id;
  bool suboptimal;
  float totalcost;
  list<modelreaction_ref> reaction_refs;
  list<string> reaction_directions;
} FBAMinimalReactionsResult;

typedef structure {
  string biomass_component;
  float mod_coefficient;
} QuantOptBiomassMod;

typedef structure {
  modelreaction_ref modelreaction_ref;
  modelcompound_ref modelcompound_ref;
  bool reaction;
  float mod_upperbound;
} QuantOptBoundMod;

typedef structure {
  float atp_synthase;
  float atp_maintenance;
  list<QuantOptBiomassMod> QuantOptBiomassMods;
  list<QuantOptBoundMod> QuantOptBoundMods;
} QuantitativeOptimizationSolution;

/*
Gapfill solution ID
@id external
*/
typedef string gapfillsol_id;

/*
Reference to a reaction object in a biochemistry
@id subws KBaseBiochem.Biochemistry.reactions.[*].id
*/
typedef string reaction_ref;

/*
Reference to a compartment object
@id subws KBaseBiochem.Biochemistry.compartments.[*].id
*/
typedef string compartment_ref;

/*
GapFillingReaction object holds data on a reaction added by gapfilling analysis

@optional compartmentIndex round
*/
typedef structure {
  int round;
  reaction_ref reaction_ref;
  compartment_ref compartment_ref;
  string direction;
  int compartmentIndex;
  list<feature_ref> candidateFeature_refs;
} GapfillingReaction;

/*
ActivatedReaction object holds data on a reaction activated by gapfilling analysis

@optional round
*/
typedef structure {
  int round;
  modelreaction_ref modelreaction_ref;
} ActivatedReaction;

/*
GapFillingSolution object holds data on a solution generated by gapfilling analysis

@optional objective gfscore actscore rejscore candscore rejectedCandidates activatedReactions failedReaction_refs

@searchable ws_subset id suboptimal integrated solutionCost koRestore_refs biomassRemoval_refs mediaSupplement_refs
*/
typedef structure {
  gapfillsol_id id;
  float solutionCost;
  list<modelcompound_ref> biomassRemoval_refs;
  list<modelcompound_ref> mediaSupplement_refs;
  list<modelreaction_ref> koRestore_refs;
  bool integrated;
  bool suboptimal;
  float objective;
  float gfscore;
  float actscore;
  float rejscore;
  float candscore;
  list<GapfillingReaction> rejectedCandidates;
  list<modelreaction_ref> failedReaction_refs;
  list<ActivatedReaction> activatedReactions;
  list<GapfillingReaction> gapfillingSolutionReactions;
} GapfillingSolution;


"""