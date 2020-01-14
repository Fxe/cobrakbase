from cobrakbase.core.kbaseobject import KBaseObjectBase
from cobrakbase.core.utils import get_id_from_ref

class NewModelTemplate(KBaseObjectBase):
    
    

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