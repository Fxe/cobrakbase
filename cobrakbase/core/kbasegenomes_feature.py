import re
from cobrakbase.core.kbaseobject import KBaseObjectBase
from cobrakbase.core.utils import get_id_from_ref


class KBaseGenomeFeature(KBaseObjectBase):
    
    @property
    def dna_sequence(self):
        return self.data['dna_sequence']
    
    @property
    def protein_translation(self):
        return self.data['protein_translation']
    
    def __str__(self):
        return self.data['id']
    
    @property
    def functions(self):
        return KBaseGenomeFeature.split_annotation(self.functions_unsplit)
    
    @property
    def functions_unsplit(self):
        functions = set([None])
        if 'functions' in self.data:
            if type(self.data['functions']) == str:
                return set([self.data['functions']])
            functions = set(self.data['functions'])
        elif 'function' in self.data:
            functions = set([self.data['function']])
        return functions
    
    @staticmethod
    def split_annotation(annotation):
        split = set()
        for s in annotation:
            if not s == None:
                for comp in re.split(' / | @ |; ', s):
                    split.add(comp)
            else:
                split.add(s)
        return split

    @staticmethod
    def split_function(function):
        split = set()
        if not function == None:
            for comp in re.split(' / | @ |; ', function):
                split.add(comp)
        else:
            split.add(s)
        return split