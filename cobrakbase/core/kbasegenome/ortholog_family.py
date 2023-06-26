import hashlib


class OrthologItem:

    def __init__(self, gene_id, order, genome):
        self.id = gene_id
        self.order = order
        self.genome = genome

    def to_kbase_data(self):
        return [self.id, self.order, str(self.genome)]

    def __str__(self):
        return f"{self.id}, {self.order}, {self.genome}"

    def __repr__(self):
        return f"{self.id}, {self.order}, {self.genome}"


class OrthologFamily:
    """
    @optional type function md5 protein_translation
    """

    def __init__(self, family_id: str, orthologs: list,
                 family_type=None, function=None, md5=None, protein_translation=None):
        """

        @param family_id: group identifier
        @param orthologs:
        @param family_type: ....
        @param function: function as described in KBaseGenomes.Genome
        @param md5: md5 encoded string of protein_translation
        @param protein_translation: protein translation string
        """
        self.id = family_id
        self.orthologs = orthologs
        self.type = family_type
        self.function = function
        self.protein_translation = protein_translation
        self._pangenome = None

    @property
    def genomes(self):
        return {o.genome for o in self.orthologs}

    @property
    def md5(self):
        if self.protein_translation is None:
            return None
        else:
            return hashlib.md5(self.protein_translation.encode("utf-8")).hexdigest()

    @property
    def gene_ids(self):
        return {o.id for o in self.orthologs}

    def __str__(self):
        return f"{self.id}: {self.function}"

    def __repr__(self):
        return f"{self.id}: {self.function}"

    def to_kbase_data(self):
        data = {
            'id': self.id,
            'orthologs': [x.to_kbase_data() for x in self.orthologs]
        }
        if self.type is not None:
            data['type'] = self.type
        if self.function is not None:
            data['function'] = self.function
        if self.protein_translation is not None:
            data['protein_translation'] = self.protein_translation
            data['md5'] = self.md5

        return data
