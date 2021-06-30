from enum import Enum


class KBaseType(Enum):

    FBAModel = 'KBaseFBA.FBAModel'
    FBAResult = 'KBaseFBA.FBA'
    Template = 'KBaseFBA.NewModelTemplate'
    Media = 'KBaseBiochem.Media'
    Genome = 'KBaseGenomes.Genome'
    ModelComparison = 'KBaseFBA.ModelComparison'

    GenomeClassifierTrainingSet = 'KBaseClassifier.GenomeClassifierTrainingSet'
    GenomeClassifier = 'KBaseClassifier.GenomeClassifier'
