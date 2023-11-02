import re
from modelseedpy.core.msgenome import MSFeature
from cobrakbase.core.kbaseobject import KBaseObjectBase
from cobrakbase.core.utils import get_id_from_ref


class KBaseGenomeFeature(MSFeature):
    def __init__(self, data):
        self.data = data
        MSFeature.__init__(
            self, self.data["id"], self.protein_translation, "; ".join(self.functions)
        )

    # @property
    # def seq(self):
    #    return self.protein_translation

    @property
    def dna_sequence(self):
        return self.data["dna_sequence"]

    @property
    def protein_translation(self):
        return self.data["protein_translation"]

    def __str__(self):
        return self.data["id"]

    @property
    def functions(self):
        return KBaseGenomeFeature.split_annotation(self.functions_unsplit)

    @property
    def functions_unsplit(self):
        functions = set()
        if "functions" in self.data:
            if type(self.data["functions"]) == str:
                return {self.data["functions"]}
            functions = set(self.data["functions"])
        elif "function" in self.data:
            functions = {self.data["function"]}
        return functions

    @staticmethod
    def split_annotation(annotation):
        split = set()
        for s in annotation:
            if s:
                for comp in re.split(" / | @ |; ", s):
                    split.add(comp)
            else:
                split.add(s)
        return split

    @staticmethod
    def split_function(function):
        split = set()
        if function:
            for comp in re.split(" / | @ |; ", function):
                split.add(comp)
        else:
            split.add(split)
        return split
