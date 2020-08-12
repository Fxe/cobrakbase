import logging
from cobrakbase.core.kbaseobject import KBaseObjectBase

logger = logging.getLogger(__name__)


class KBasePangenome(KBaseObjectBase):

    def __init__(self, data, api=None):
        super().__init__(data, api)
        self.genome_ref_object_info = {}
        self.genome_ref_genome = {}  # Genome Object corresponding to the genome_ref
        for genome_ref in self.data['genome_refs']:
            self.genome_ref_object_info[genome_ref] = None
            if self.api:
                logging.debug('[%s] loading genome_ref info from api [%s]', self.id, self.api)
                info = api.get_object_info_from_ref(genome_ref)
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
