import logging
from cobra.core.dictlist import DictList
from cobrakbase.kbase_object_info import KBaseObjectInfo
from cobrakbase.core.kbasegenome.ortholog_family import OrthologFamily, OrthologItem
from cobrakbase.core.kbaseobject import KBaseObject

logger = logging.getLogger(__name__)


class KBasePangenome(KBaseObject):


    def __init__(self, pangenome_id: str, name: str, pangenome_type: str, genome_refs: list, info=None, args=None):
        if info is None:
            info = KBaseObjectInfo(None, 'KBaseGenomes.Pangenome')
        super().__init__({}, info, args)
        self.id = pangenome_id
        self.name = name
        self.type = pangenome_type
        self.genome_refs = genome_refs
        self.api = None
        self.orthologs = DictList()
        self.genome_ref_object_info = {}
        self.genome_ref_genome = {}  # Genome Object corresponding to the genome_ref
        self.load_tax_info()

    def add_orthologs(self, ortholog_list: list):
        """

        :param ortholog_list:
        :return:
        """
        duplicates = list(filter(lambda o: o.id in self.orthologs, ortholog_list))
        if len(duplicates) > 0:
            raise ValueError(
                f"unable to add orthologs {duplicates} already present in the pangenome"
            )

        for f in ortholog_list:
            f._pangenome = self

        self.orthologs += ortholog_list

    def load_tax_info(self):
        for genome_ref in self.data["genome_refs"]:
            self.genome_ref_object_info[genome_ref] = None
            if self.api:
                logging.debug(
                    "[%s] loading genome_ref info from api [%s]", self.id, self.api
                )
                info = self.api.get_object_info_from_ref(genome_ref)
                self.genome_ref_object_info[genome_ref] = info
                logging.debug("[%s] %s -> %s", self.id, genome_ref, info.id)

    @staticmethod
    def from_kbase_json(data, info=None, args=None, api=None):
        pangenome = KBasePangenome(data['id'], data['name'], data['type'], data['genome_refs'], info, args)
        orthologs = []
        for o in data['orthologs']:
            items = [OrthologItem(i[0], i[1], i[2]) for i in o['orthologs']]
            family = OrthologFamily(o['id'], items, o.get('type'), o.get('function'), o.get('md5'),
                                    o.get('protein_translation'))
            orthologs.append(family)
        pangenome.add_orthologs(orthologs)

        return pangenome

    @property
    def ortholog_ids(self):
        return list(map(lambda x: x["id"], self.data["orthologs"]))

    def get_ortholog_by_id(self, ortholog_id):
        res = list(filter(lambda x: x["id"] == ortholog_id, self.data["orthologs"]))
        if len(res) < 1:
            return None
        return res[0]

    def get_ortholog_by_index(self, ortholog_index):
        return self.data["orthologs"][ortholog_index]

    def _to_json(self):
        data = {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'genome_refs': [str(s) for s in self.genome_refs],
            'orthologs': [o.to_kbase_data() for o in self.orthologs]
        }

        return data

    def _repr_html_(self):
        return """
        <table>
            <tr>
                <td><strong>ID</strong></td>
                <td>{id}</td>
            </tr><tr>
                <td><strong>Name</strong></td>
                <td>{name}</td>
            </tr><tr>
                <td><strong>Type</strong></td>
                <td>{type}</td>
            </tr><tr>
                <td><strong>Genomes</strong></td>
                <td>{num_genomes}</td>
            </tr><tr>
                <td><strong>Orthologs</strong></td>
                <td>{num_orthologs}</td>
            </tr>
          </table>""".format(
            id=self.id,
            address="0x0%x" % id(self),
            name=self.name,
            type=self.type,
            num_genomes=len(self.genome_refs),
            num_orthologs=len(self.orthologs)
        )
