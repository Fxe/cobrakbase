from pandas import DataFrame
from cobrakbase.exceptions import ObjectError


class FloatMatrix2D:
    def __init__(self, data: DataFrame):
        self._validate(data)
        self.data = data

    @staticmethod
    def _validate(data):
        col_ids = set()
        for x in data.columns.to_list():
            if x not in col_ids:
                col_ids.add(x)
            else:
                raise ObjectError("duplicate column ID: " + x)
        row_ids = set()
        for x in data.index.to_list():
            if x not in row_ids:
                row_ids.add(x)
            else:
                raise ObjectError("duplicate row ID: " + x)
        # TODO: validate data to check for float?
        return True

    @staticmethod
    def from_kbase_data(data):
        df = DataFrame(data["values"], columns=data["col_ids"], index=data["row_ids"])
        return df

    @property
    def column_ids(self):
        return self.data.columns.to_list()

    @property
    def row_ids(self):
        return self.data.index.to_list()

    def get_kbase_data(self):
        return {
            "values": self.data.to_numpy().tolist(),
            "row_ids": self.row_ids,
            "col_ids": self.column_ids,
        }

    def __repr__(self):
        return self.data.__repr__()

    def _repr_html_(self):
        return self.data._repr_html_()
