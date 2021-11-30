from pandas import DataFrame
from cobrakbase.kbase_object_info import KBaseObjectInfo


class ExpressionMatrix:
    """
  /*
  A wrapper around a FloatMatrix2D designed for simple matricies of Expression
  data.  Rows map to features, and columns map to conditions.  The data type 
  includes some information about normalization factors and contains
  mappings from row ids to features and col ids to conditions.

  description - short optional description of the dataset
  type - ? level, ratio, log-ratio
  scale - ? probably: raw, ln, log2, log10
  col_normalization - mean_center, median_center, mode_center, zscore
  row_normalization - mean_center, median_center, mode_center, zscore
  feature_mapping - map from row_id to feature id in the genome
  data - contains values for (feature,condition) pairs, where 
      features correspond to rows and conditions are columns
      (ie data.values[feature][condition])
  @optional description row_normalization col_normalization
  @optional genome_ref feature_mapping conditionset_ref condition_mapping report

  @metadata ws type
  @metadata ws scale
  @metadata ws row_normalization
  @metadata ws col_normalization
  @metadata ws genome_ref as Genome
  @metadata ws conditionset_ref as ConditionSet
  @metadata ws length(data.row_ids) as feature_count
  @metadata ws length(data.col_ids) as condition_count
  */
  typedef structure {
    string description;
    string type;
    string scale;
    string row_normalization;
    string col_normalization;
    ws_genome_id genome_ref;
    mapping<string, string> feature_mapping;
    ws_conditionset_id conditionset_ref;
    mapping<string, string> condition_mapping;
    FloatMatrix2D data;
    AnalysisReport report;
  } ExpressionMatrix;
  """

    OBJECT_TYPE = 'KBaseFeatureValues.ExpressionMatrix'

    def __init__(self, data: DataFrame, scale, matrix_type, genome_ref=None, feature_mapping=None, description=None,
                 row_normalization=None, col_normalization=None, info=None, args=None):
        self.data = data
        self.description = description
        self.row_normalization = row_normalization
        self.col_normalization = col_normalization
        self.feature_mapping = feature_mapping
        self.genome_ref = genome_ref
        self.scale = scale
        self.type = matrix_type
        self.info = info if info else KBaseObjectInfo(object_type=ExpressionMatrix.OBJECT_TYPE)
        self.args = args

    @staticmethod
    def from_dict(data, info=None, args=None):
        expression_data = DataFrame(data['data']['values'],
                                    columns=data['data']['col_ids'],
                                    index=data['data']['row_ids'])
        genome_ref = data['genome_ref'] if 'genome_ref' in data else None
        feature_mapping = data['feature_mapping'] if 'feature_mapping' in data else None
        description = data['description'] if 'description' in data else None
        row_normalization = data['row_normalization'] if 'row_normalization' in data else None
        col_normalization = data['col_normalization'] if 'col_normalization' in data else None
        if info is None:
            info = KBaseObjectInfo(object_type=ExpressionMatrix.OBJECT_TYPE)

        return ExpressionMatrix(expression_data, data['scale'], data['type'], genome_ref, feature_mapping, description,
                                row_normalization, col_normalization, info, args)

    def __repr__(self):
        return self.data.__repr__()

    def _repr_html_(self):
        return self.data._repr_html_()

    def get_data(self):
        kbase_data = {
            'data': {
                'values': self.data.to_numpy().tolist(),
                'row_ids': self.data.index.to_list(),
                'col_ids': self.data.columns.to_list()
            },
            'scale': self.scale,
            'type': self.type
        }
        if self.genome_ref:
            kbase_data['genome_ref'] = self.genome_ref
        if self.feature_mapping:
            kbase_data['feature_mapping'] = self.feature_mapping
        if self.description:
            kbase_data['description'] = self.description
        if self.row_normalization:
            kbase_data['row_normalization'] = self.row_normalization
        if self.col_normalization:
            kbase_data['col_normalization'] = self.col_normalization
        return kbase_data
