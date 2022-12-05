from cobrakbase.core.kbaseobject import KBaseObjectBase


class OrthologFamily(KBaseObjectBase):
    def __init__(self, data, pangenome=None):
        super().__init__(data, None)

    @property
    def genomes(self):
        return set(map(lambda x: x[2], self.data["orthologs"]))

    @property
    def function(self):
        return self.data["function"]

    def __str__(self):
        return f"{self.id}: {self.function}"

    def __repr__(self):
        return f"{self.id}: {self.data['function']}"
