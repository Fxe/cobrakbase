from cobrakbase.core.kbaseobject import KBaseObjectBase
from cobrakbase.core.utils import get_id_from_ref

class ChemicalAbundanceMatrix(KBaseObjectBase):
    
    def get_chemical_abundance_data(self, dataset, mapping, attr = 'seed_id'):
        col_index = None
        result = {}
        try:
            col_index = self.data['data']['col_ids'].index(dataset)
        except ValueError:
            return None
        
        seed_id_index = 0
        if not mapping == None:
            for i in range(len(mapping['attributes'])):
                a = mapping['attributes'][i]
                if a['attribute'] == attr:
                    seed_id_index = i
                
        for i in range(len(self.data['data']['row_ids'])):
            k = self.data['data']['row_ids'][i]
            v = self.data['data']['values'][i][col_index]
            if not v == None:
                if mapping == None:
                    result[k] = v
                elif k in mapping['instances'] and not len(mapping['instances'][k][seed_id_index]) == 0:
                    attr_val = mapping['instances'][k][seed_id_index]
                    for maybe_seed_id in attr_val.split(';'):
                        result[maybe_seed_id] = v
                else:
                    result[k] = v

        return result

    def get_all_chemical_abundance_data(self, data, mapping, attr = 'seed_id'):
        result = {}
        for dataset in data['data']['col_ids']:
            chemical_abundance = self.get_chemical_abundance_data(dataset, mapping, attr)
            if len(chemical_abundance) > 0:
                result[dataset] = chemical_abundance

        return result