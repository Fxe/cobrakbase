import cobrakbase
from cobra.core.dictlist import DictList
from cobrakbase.core.kbaseobject import KBaseObject
from cobrakbase.core.kbaseobject import AttrDict
from cobrakbase.core.utils import get_id_from_ref

class ChemicalAbundanceMatrix(KBaseObject):
    
    def __init__(self, data=None, info=None, args=None):
        super().__init__(data, info, args, 'KBaseMatrices.ChemicalAbundanceMatrix')
        self.attributes = []
        self.peaks = DictList()
        for i in range(len(self.data['_data']['row_ids'])):
            values = {}
            for j in range(len(self.data['_data']['col_ids'])):
                values[self.data['_data']['col_ids'][j]] = self.data['_data']['values'][i][j]
            peak = AttrDict({
                "id" : self.data['_data']['row_ids'][i],
                "values" : values,
                "attributes" : {}
            })
            self.peaks.append(peak)
            
        if "row_attributemapping_ref" in data:
            kbase_api = cobrakbase.KBaseAPI()
            mapping = kbase_api.get_from_ws(self.row_attributemapping_ref)
            attr_index = 0
            for attr in mapping.attributes:
                att_name = None
                if type(attr) == "str":
                    att_name = attr
                    self.attributes.append(attr)
                else:
                    att_name = attr["attribute"]
                    self.attributes.append(attr["attribute"])
                for peak in self.peaks:
                    if peak.id in mapping.instances:
                        peak.attributes[att_name] = mapping.instances[peak.id][attr_index]
                attr_index += 1
    
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
    
    def map_to_modelseed(self,modelseed,suffix = ""):
        formula_hash = {}
        smiles_hash = {}
        base_inchikey_hash = {}
        kegg_hash = {}
        output_hash = {}
        for cpdid in modelseed.compound_aliases:
            if "kegg" in modelseed.compound_aliases[cpdid]:
                for keggid in modelseed.compound_aliases[cpdid]["kegg"]:
                    if keggid not in output_hash[keggid]:
                        kegg_hash[keggid]  = []
                    kegg_hash[keggid].append(keggid)
        
        for compound in modelseed.compounds:
            if "smiles" in compound:
                if compound["smiles"] not in smiles_hash:
                    smiles_hash[compound["smiles"]] = []
                smiles_hash[compound["smiles"]].append(compound['id'])
            if "formula" in compound:
                if compound["formula"] not in formula_hash:
                    formula_hash[compound["formula"]] = []
                formula_hash[compound["formula"]].append(compound['id'])
            if "inchikey" in compound:
                array = compound["inchikey"].split("-")
                if array[0] not in base_inchikey_hash:
                    base_inchikey_hash[array[0]] = []
                base_inchikey_hash[array[0]].append(compound['id'])
        for peak in self.peaks:
            if "modelseed" in peak.attributes and len(peak.attributes["modelseed"]) > 0:
                output_hash[peak.id] = [peak.attributes["modelseed"]+suffix]
            elif "kegg" in peak.attributes and len(peak.attributes["kegg"]) > 0:
                if peak.attributes["kegg"] in kegg_hash:
                    for item in kegg_hash[peak.attributes["kegg"]]:
                        if peak.id not in output_hash or item+suffix not in output_hash[peak.id]:
                            output_hash[peak.id].append(item+suffix)
            elif "inchikey" in peak.attributes and len(peak.attributes["inchikey"]) > 0:
                array = peak.attributes["inchikey"].split("-")
                if array[0] in base_inchikey_hash:
                    for item in base_inchikey_hash[array[0]]:
                        if peak.id not in output_hash or item+suffix not in output_hash[peak.id]:
                            output_hash[peak.id].append(item+suffix)
            elif "smiles" in peak.attributes and len(peak.attributes["smiles"]) > 0:
                if peak.attributes["smiles"] in smiles_hash:
                    for item in smiles_hash[peak.attributes["smiles"]]:
                        if peak.id not in output_hash or item not in output_hash[peak.id]:
                            output_hash[peak.id].append(item+suffix)
            elif "formula" in peak.attributes and len(peak.attributes["formula"]) > 0:
                if peak.attributes["formula"] in formula_hash:
                    for item in formula_hash[peak.attributes["formula"]]:
                        if peak.id not in output_hash or item not in output_hash[peak.id]:
                            output_hash[peak.id].append(item+suffix)
        return output_hash