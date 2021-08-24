from cobrakbase.core.kbaseobject import KBaseObjectBase
from cobrakbase.core.utils import get_id_from_ref

from cobra.core.dictlist import DictList

class NewModelTemplate(KBaseObjectBase):

    def __init__(self, id_or_model=None, name=None):
        if isinstance(id_or_model, Model):
            Object.__init__(self, name=name)
            self.__setstate__(id_or_model.__dict__)
            if not hasattr(self, "name"):
                self.name = None
            self._solver = id_or_model.solver
        else:
            Object.__init__(self, id_or_model, name=name)
            
            self.compcompounds = DictList()
    
    def new(id, name):
        return {
            'biochemistry_ref': "489/6/6",
            'biomasses': [],
            'compartments': [],
            'compcompounds': [],
            'complexes': [],
            'compounds': [],
            'domain': [],
            'id': id,
            'name': name,
            'pathways': [],
            'reactions': [],
            'roles': [],
            'subsystems': [],
            'type': "GenomeScale",
        }