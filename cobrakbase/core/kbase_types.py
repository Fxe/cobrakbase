from enum import Enum


class KBaseType(Enum):

    FBAModel = 'KBaseFBA.FBAModel'
    FBAResult = 'KBaseFBA.FBA'
    Template = 'KBaseFBA.NewModelTemplate'
    Media = 'KBaseBiochem.Media'
    Genome = 'KBaseGenomes.Genome'
    ModelComparison = 'KBaseFBA.ModelComparison'
    EscherMap = 'KBaseFBA.EscherMap'

    GenomeClassifierTrainingSet = 'KBaseClassifier.GenomeClassifierTrainingSet'
    GenomeClassifier = 'KBaseClassifier.GenomeClassifier'
