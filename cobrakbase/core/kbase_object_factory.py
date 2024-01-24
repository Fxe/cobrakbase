import json
import logging
from cobrakbase.kbase_object_info import KBaseObjectInfo
from cobrakbase.core.kbaseobject import KBaseObject
from cobrakbase.core.kbasebiochem import Media
from cobrakbase.core.kbasefba.fbamodel_builder import FBAModelBuilder
from cobrakbase.core.kbasefba.newmodeltemplate_builder import NewModelTemplateBuilder
from cobrakbase.core.kbasegenome.genome import KBaseGenome
from cobrakbase.core.kbasegenome.pangenome import KBasePangenome
from cobrakbase.core.kbasematrices.chemicalabundancematrix import (
    ChemicalAbundanceMatrix,
)
from cobrakbase.core.kbasefba.eschermap import EscherMap
from cobrakbase.core.kbaseclassifier.genomeclassifiertrainingset import (
    GenomeClassifierTrainingSet,
)
from cobrakbase.core.kbaseclassifier.genomeclassifier import GenomeClassifier
from cobrakbase.core.kbasefeaturevalues.expressionmatrix import ExpressionMatrix
from cobrakbase.core.kbaseexperiments.attributemapping import AttributeMapping

logger = logging.getLogger(__name__)


def _build_model(x, y, z):
    return FBAModelBuilder.from_kbase_json(x, y, z).build()


def _build_template(x, y, z):
    return NewModelTemplateBuilder.from_dict(x, y, z).build()


def _build_escher_map(x, y, z):
    return EscherMap.from_dict(x, y, z)


class KBaseObjectFactory:
    """
    New class to build objects from workspace - converts base object fields into attributes
    and sticks sub objects into dictlists
    """

    def __init__(self):
        self.object_mapper = {
            "KBaseFBA.FBAModel": _build_model,
            "KBaseFBA.NewModelTemplate": _build_template,
            # add FBA
            "KBaseFBA.EscherMap": _build_escher_map,
            "KBaseBiochem.Media": Media,
            KBaseGenome.OBJECT_TYPE: KBaseGenome.from_kbase_data,
            "KBaseGenomes.Pangenome": KBasePangenome,
            ChemicalAbundanceMatrix.OBJECT_TYPE: ChemicalAbundanceMatrix.from_dict,
            "KBaseClassifier.GenomeClassifierTrainingSet": GenomeClassifierTrainingSet,
            "KBaseClassifier.GenomeClassifier": GenomeClassifier,
            "KBaseFeatureValues.ExpressionMatrix": ExpressionMatrix.from_dict,
            AttributeMapping.OBJECT_TYPE: AttributeMapping.from_dict,
        }

    def build_object_from_file(self, filename, object_type):
        with open(filename) as json_file:
            data = json.load(json_file)
            return self._build_object(object_type, data, None, None)

    def _build_object(self, object_type, data, info, args):
        if object_type in self.object_mapper:
            if 'from_kbase_json' in dir(self.object_mapper[object_type]):
                logger.debug(f"using [{object_type}] from_kbase_json builder")
                return self.object_mapper[object_type].from_kbase_json(data, info, args)
            else:
                logger.debug("using old default builder")
                return self.object_mapper[object_type](data, info, args)
        else:
            logger.debug("using default KBaseObject builder")
            return KBaseObject(data, info, args, object_type)

    def build_object_from_ws(self, ws_output, object_type):
        if ws_output is None:
            return KBaseObject(None, None, None, object_type)

        ws_data = ws_output["data"][0]

        args = {}
        fields = [
            "provenance",
            "path",
            "creator",
            "orig_wsid",
            "created",
            "epoch",
            "refs",
            "copied",
            "copy_source_inaccessible",
        ]
        for field in fields:
            if field in ws_data:
                args[field] = ws_data[field]
        data = ws_data["data"]
        info = KBaseObjectInfo(ws_data["info"])

        if info and info.type and info.type in self.object_mapper:
            return self._build_object(info.type, data, info, args)

        return KBaseObject(data, info, args)

    def create(self, ws_output, object_type):
        """
        
        """
        return self.build_object_from_ws(ws_output, object_type)
