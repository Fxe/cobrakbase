import logging
from cobrakbase.core.kbasegenome.ortholog_family import OrthologFamily
from cobrakbase.core.kbaseobject import KBaseObject

logger = logging.getLogger(__name__)


class KBasePangenome(KBaseObject):

    def __init__(self, data=None, info=None, args=None):
        super().__init__(data, info, args)
        self.api = None
        self.genome_ref_object_info = {}
        self.genome_ref_genome = {}  # Genome Object corresponding to the genome_ref
        self.load_tax_info()

    def load_tax_info(self):
        for genome_ref in self.data['genome_refs']:
            self.genome_ref_object_info[genome_ref] = None
            if self.api:
                logging.debug('[%s] loading genome_ref info from api [%s]', self.id, self.api)
                info = self.api.get_object_info_from_ref(genome_ref)
                self.genome_ref_object_info[genome_ref] = info
                logging.debug('[%s] %s -> %s', self.id, genome_ref, info.id)

    @property
    def ortholog_ids(self):
        return list(map(lambda x: x['id'], self.data['orthologs']))

    def get_ortholog_by_id(self, ortholog_id):
        res = list(filter(lambda x: x['id'] == ortholog_id, self.data['orthologs']))
        if len(res) < 1:
            return None
        return res[0]

    def get_ortholog_by_index(self, ortholog_index):
        return self.data['orthologs'][ortholog_index]


    def _to_object(self, key, data):
        if key == 'orthologs':
            return OrthologFamily(data, self)

        return super()._to_object(key, data)
