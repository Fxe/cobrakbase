from cobrakbase.core.kbasematrices.float_matrix_2d import FloatMatrix2D
from cobrakbase.kbase_object_info import KBaseObjectInfo
from cobra.core.dictlist import DictList
from cobrakbase.core.kbaseobject import AttrDict
from cobrakbase.exceptions import ObjectError


class ChemicalAbundanceMatrix(FloatMatrix2D):
    """
    A wrapper around a FloatMatrix2D designed for matrices of chemical concentration data. The
    columns represent experimental conditions while the rows correspond to individual
    identified metabolites

    KBaseMatrices Fields:
    col_normalization - mean_center, median_center, mode_center, zscore
    row_normalization - mean_center, median_center, mode_center, zscore
    col_mapping - map from col_id to an id in the col_condition_set
    row_mapping - map from row_id to a id in the row_condition_set
    col_attributemapping_ref - a reference to a AttributeMapping that relates to the columns
    row_attributemapping_ref - a reference to a AttributeMapping that relates to the rows
    attributes - a mapping of additional information pertaining to the object
    search_attributes - a mapping of object information used by search

    data - contains values for (compound,condition) pairs, where
           compounds correspond to rows and conditions are columns
           (ie data.values[compound][condition])

    Additional Fields:
    biochemistry_ref - a reference to a biochemistry object
    biochemistry_mapping - map from row_id to a set compound ids in a biochemistry object

    Validation:
    @unique data.row_ids
    @unique data.col_ids
    @conditionally_required row_attributemapping_ref row_mapping
    @conditionally_required col_attributemapping_ref col_mapping
    @contains data.row_ids row_mapping
    @contains data.col_ids col_mapping
    @contains values(row_mapping) row_attributemapping_ref:instances
    @contains values(col_mapping) col_attributemapping_ref:instances
    @contains values(biochemistry_mapping) biochemistry_ref:compounds.[*].id

    @metadata ws scale
    @metadata ws unit
    @metadata ws type
    @metadata ws row_normalization
    @metadata ws col_normalization
    @metadata ws col_attributemapping_ref as col_attribute_mapping
    @metadata ws row_attributemapping_ref as row_attribute_mapping
    @metadata ws sample_set_ref as sample_set
    @metadata ws length(data.row_ids) as compound_count
    @metadata ws length(data.col_ids) as sample_count

    typedef structure {
      string scale; raw, ln, log2, log10
      FloatMatrix2D data;
      ws_attributemapping_id row_attributemapping_ref;
      (Optional) string description; short optional description of the dataset
      (Optional) string row_normalization;
      (Optional) string col_normalization;
      (Optional) mapping<string, string> col_mapping;
      (Optional) ws_attributemapping_id col_attributemapping_ref;
      (Optional) mapping<string, string> row_mapping;
      (Optional) mapping<string, string> attributes;
      (Optional) list<string> search_attributes;
      (Optional) ws_ref biochemistry_ref;
      mapping<string, list<string>> biochemistry_mapping;
      (Optional) ws_ref sample_set_ref;
      (Optional) string unit;
      (Optional) string type;
    } ChemicalAbundanceMatrix;
    """

    OBJECT_TYPE = 'KBaseMatrices.ChemicalAbundanceMatrix'
    
    def __init__(self, data, scale, biochemistry_ref, row_attribute_mapping,
                 matrix_type=None, row_mapping=None, description=None, unit=None,
                 sample_set_ref=None, info=None, args=None):
        """
        super().__init__(data, info, args, 'KBaseMatrices.ChemicalAbundanceMatrix')
        self.row_attributemapping_ref = None
        self.attributes = []
            
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
        """
        super().__init__(data)
        self.description = description
        self.scale = scale
        self.type = matrix_type

        self.row_attribute_mapping = row_attribute_mapping
        self.row_mapping = row_mapping

        self.sample_set_ref = sample_set_ref
        self.biochemistry_ref = biochemistry_ref
        self.unit = unit

        self.info = info if info else KBaseObjectInfo(object_type=ChemicalAbundanceMatrix.OBJECT_TYPE)
        self.args = args

    @property
    def peaks(self):
        peaks = DictList()
        for i in range(len(self.data['_data']['row_ids'])):
            values = {}
            for j in range(len(self.data['_data']['col_ids'])):
                values[self.data['_data']['col_ids'][j]] = self.data['_data']['values'][i][j]
            peak = AttrDict({
                "id" : self.data['_data']['row_ids'][i],
                "values" : values,
                "attributes" : {}
            })
            peaks.append(peak)
        return peaks

    @staticmethod
    def from_dict(data, info=None, args=None):
        matrix_data = FloatMatrix2D.from_kbase_data(data['data'])
        description = data['description'] if 'description' in data else None
        matrix_type = data['type'] if 'type' in data else None
        unit = data['unit'] if 'unit' in data else None
        sample_set_ref = data['sample_set_ref'] if 'sample_set_ref' in data else None
        row_mapping = data['row_mapping'] if 'row_mapping' in data else None

        if info is None:
            info = KBaseObjectInfo(object_type=ChemicalAbundanceMatrix.OBJECT_TYPE)
        return ChemicalAbundanceMatrix(matrix_data, data['scale'], data['biochemistry_ref'],
                                       data['row_attributemapping_ref'],
                                       matrix_type, row_mapping, description, unit,
                                       sample_set_ref, info, args)

    def get_data(self):
        kbase_data = {
            'data': super().get_kbase_data(),
            'scale': self.scale,
            'biochemistry_ref': self.biochemistry_ref
        }
        if self.description:
            kbase_data['description'] = self.description
        if self.sample_set_ref:
            kbase_data['sample_set_ref'] = self.sample_set_ref
        if self.type:
            kbase_data['type'] = self.type
        if self.row_mapping:
            kbase_data['row_mapping'] = self.row_mapping
        if self.row_attribute_mapping:
            if type(self.row_attribute_mapping) is str:
                kbase_data['row_attributemapping_ref'] = self.row_attribute_mapping
            elif self.row_attribute_mapping.info.reference:
                kbase_data['row_attributemapping_ref'] = self.row_attribute_mapping.info.reference
            else:
                raise ObjectError("Invalid row_attribute_mapping, object info not mapped to KBase reference ?")
        return kbase_data

    def __repr__(self):
        return self.data.__repr__()

    def _repr_html_(self):
        return self.data._repr_html_()
    
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