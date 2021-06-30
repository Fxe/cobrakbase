import json
from cobrakbase.kbase_object_info import KBaseObjectInfo
from cobrakbase.core.kbaseobject import KBaseObject
from cobrakbase.core.kbasebiochem import Media
from cobrakbase.core.kbasefba.fbamodel_builder import FBAModelBuilder
from cobrakbase.core import KBaseGenome
from cobrakbase.core.kbasegenome.pangenome import KBasePangenome
from cobrakbase.core.kbasematrices.chemicalabundancematrix import ChemicalAbundanceMatrix
from cobrakbase.core.kbasefba.newmodeltemplate import NewModelTemplate
from cobrakbase.core.kbaseclassifier.genomeclassifiertrainingset import GenomeClassifierTrainingSet
from cobrakbase.core.kbaseclassifier.genomeclassifier import GenomeClassifier


def _build_model(x, y, z):
    return FBAModelBuilder.from_kbase_json(x, y, z).build()


class KBaseObjectFactory:
    """
    New class to build objects from workspace - converts base object fields into attributes
    and sticks sub objects into dictlists
    """
    def __init__(self):

        self.object_mapper = {
            'KBaseFBA.FBAModel': _build_model,
            'KBaseFBA.NewModelTemplate': NewModelTemplate,
            # add FBA
            'KBaseBiochem.Media': Media,
            'KBaseGenomes.Genome': KBaseGenome,
            'KBaseGenomes.Pangenome': KBasePangenome,
            'KBaseMatrices.ChemicalAbundanceMatrix': ChemicalAbundanceMatrix,
            'KBaseClassifier.GenomeClassifierTrainingSet': GenomeClassifierTrainingSet,
            'KBaseClassifier.GenomeClassifier': GenomeClassifier
        }
    
    def build_object_from_file(self, filename, object_type):
        with open(filename) as json_file:
            data = json.load(json_file)
            
        if object_type in self.object_mapper:
            return self.object_mapper[object_type](data, None, None)
        
        return KBaseObject(data, None, None, object_type)
    
    def build_object_from_ws(self, ws_output, object_type):
        if ws_output is None:
            return KBaseObject(None, None, None, object_type)

        args = {}
        fields = ["provenance", "path", "creator", "orig_wsid", "created", "epoch", "refs", "copied",
                  "copy_source_inaccessible"]
        for field in fields:
            if field in ws_output["data"][0]:
                args[field] = ws_output["data"][0][field]
        data = ws_output["data"][0]["data"]
        info = KBaseObjectInfo(ws_output["data"][0]["info"])

        if info and info.type and info.type in self.object_mapper:
            return self.object_mapper[info.type](data, info, args)

        return KBaseObject(data, info, args)

    def create(self, ws_output, object_type):
        return self.build_object_from_ws(ws_output, object_type)
