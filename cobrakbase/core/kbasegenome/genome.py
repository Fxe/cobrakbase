import logging
from cobra.core.dictlist import DictList
from cobrakbase.core.kbaseobject import KBaseObject
from cobrakbase.kbase_object_info import KBaseObjectInfo
from modelseedpy.core.msgenome import MSGenome
from cobrakbase.core.kbasegenome.genome_cds_feature import (
    KBaseGenomeFeature,
    KBaseGenomeCDS,
)

logger = logging.getLogger(__name__)


class KBaseGenome(KBaseObject, MSGenome):
    """
    Genome type -- annotated and assembled genome data.
    """

    OBJECT_TYPE = "KBaseGenomes.Genome"

    def __init__(
        self,
        genome_id: str,
        scientific_name: str,
        domain: str,
        genome_tiers: list,
        feature_counts: dict,
        genetic_code: int,
        dna_size: int,
        num_contigs: int,
        molecule_type: str,
        source: str,
        md5: str,
        gc_content: float,
        taxonomy=None,
        assembly_ref=None,
        taxon_ref=None,
        info=None,
        args=None,
    ):
        """
                Features vs. coding sequences: a feature is a sequence in the DNA that codes
        for a protein, including non-transcribed introns. A coding sequence (stored as
        `cdss`) includes **only** the sections of the feature that codes for a protein,
        minus introns and UTRs.

            warnings - list of string - genome-level warnings generated in the annotation process
            contig_lengths - list of int - nucleotide length of each contig in the genome
                Indexes in this list correspond to indexes in the `contig_ids` list.
            contig_ids - list of str - external database identifiers for each contig (eg. "NC_000913.3")
            source_id - string - identifier of this genome from the source database (eg. the RefSeq ID such as "NC_000913")
            taxon_assignments - mapping of taxonomy namespace to taxon ID.
                example - {"ncbi": "286", "gtdb": "s__staphylococcus_devriesei"}
            publications - tuple of (pubmedid, source, title, web_addr, year, authors, journal). See typedef above.
            ontology_events - A record of the service and method used for a set of
                ontology assignments on the genome.
            ontologies_present - a mapping of ontology source id (eg. "GO") to a mapping
                of term IDs (eg "GO:16209") to term names (eg. "histidine biosynthetic process").
            mrnas - array of transcribed messenger RNA sequences (equal to cdss plus 5' and 3' UTRs)
            non_coding_features - array of features that does not include mRNA, CDS, and protein-encoding genes
            genbank_handle_ref - file server handle reference to the source genbank file for this genome.
            gff_handle_ref - file server handle reference to the source GFF file for this genome.
            external_source_origination_date - TODO look at GFU for this
            release - string - User-supplied release or version of the source data. This
                most likely will come from an input field in the import app.
            original_source_file_name - filename from which this genome was derived (eg. genbank or gff filename).
            notes - TODO
            quality_scores - TODO
            suspect - bool - flag of whether this annotation is problematic due to some warning
            genome_type - string - controlled vocab - One of "draft isolate",
                "finished isolate", "mag", "sag", "virus", "plasmid", "construct"

        @metadata ws gc_content as GC content
        @metadata ws taxonomy as Taxonomy
        @metadata ws md5 as MD5
        @metadata ws dna_size as Size
        @metadata ws genetic_code as Genetic code
        @metadata ws domain as Domain
        @metadata ws source_id as Source ID
        @metadata ws source as Source
        @metadata ws scientific_name as Name
        @metadata ws genome_type as Genome Type
        @metadata ws length(features) as Number of Protein Encoding Genes
        @metadata ws length(cdss) as Number of CDS
        @metadata ws assembly_ref as Assembly Object
        @metadata ws num_contigs as Number contigs
        @metadata ws length(warnings) as Number of Genome Level Warnings
        @metadata ws suspect as Suspect Genome

          @optional mapping<string, string> taxon_assignments;
          @optional list<publication> publications;
          @optional list<Ontology_event> ontology_events;
          @optional mapping<string, mapping<string, string>> ontologies_present;
          @optional source_id source_id;
          @optional list<NonCodingFeature> non_coding_features;
          @optional list<mRNA> mrnas;
          @optional genbank_handle_ref genbank_handle_ref;
          @optional gff_handle_ref gff_handle_ref;
          @optional string external_source_origination_date;
          @optional string release;
          @optional string original_source_file_name;
          @optional string notes;
          @optional list<GenomeQualityScore> quality_scores;
          @optional Bool suspect;
          @optional string genome_type;
          @optional list<string> warnings;
          @optional list<int> contig_lengths;
          @optional list<string> contig_ids;

                @param genome_id: genome identifier
                @param features: protein coding genes (see the separate Feature spec)
                @param cdss: protein-coding sequences
                @param scientific_name: species name
                @param domain: phylogenetic domain name (eg. "Bacteria")
                @param genome_tiers: controlled vocabulary (based on app input and checked by GenomeFileUtil)
                A list of labels describing the data source for this genome.
                Allowed values - Representative, Reference, ExternalDB, User
                Tier assignments based on genome source:
                 * All phytozome - Representative and ExternalDB
                 * Phytozome flagship genomes - Reference, Representative and ExternalDB
                 * Ensembl - Representative and ExternalDB
                 * RefSeq Reference - Reference, Representative and ExternalDB
                 * RefSeq Representative - Representative and ExternalDB
                 * RefSeq Latest or All Assemblies folder - ExternalDB
                 * User Data - User tagged
                @param feature_counts: map of string to integer - total counts of each type of feature
                keys are a controlled vocabulary of - "CDS", "gene", "misc_feature",
                "misc_recomb", "mobile_element", "ncRNA" - 72, "non_coding_features",
                "non_coding_genes", "protein_encoding_gene", "rRNA", "rep_origin",
                "repeat_region", "tRNA"
                @param genetic_code: An NCBI-assigned taxonomic category for the organism
                See here - https://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi
                @param dna_size: total number of nucleotides
                @param num_contigs: total number of contigs in the genome
                @param molecule_type: controlled vocab - the type of molecule sequenced
                Possible values are "Unknown", "DNA", "RNA", "genomic DNA", "genomic RNA",
                "mRNA", "tRNA", "rRNA", "other RNA", "other DNA", "transcribed RNA",
                "viral cRNA", "unassigned DNA", "unassigned RNA"
                @param source: controlled vocab - descriptor of where this data came from (eg. "RefSeq")
                Allowed entries RefSeq, Ensembl, Phytozome, RAST, Prokka, User_upload
                @param md5: checksum of the underlying assembly sequence
                @param gc_content: ratio of GC count to AT in the genome
                @param taxonomy: semicolon-delimited taxonomy lineage, in order of parent to child
                @param assembly_ref: workspace reference to an assembly object from which this annotated genome was derived
                @param taxon_ref: workspace reference to a taxon object that classifies the species or strain of this genome
                @param info: KBase object info
                @param args: KBase workspace args
        """

        if info is None:
            info = KBaseObjectInfo(object_type="KBaseGenomes.Genome")
        KBaseObject.__init__(self, {}, info, args, info.type, ["ontology_events"])
        MSGenome.__init__(self)
        self.id = genome_id
        self.scientific_name = scientific_name
        self.domain = domain
        self.genome_tiers = genome_tiers
        self.feature_counts = feature_counts
        self.genetic_code = genetic_code
        self.dna_size = dna_size
        self.num_contigs = num_contigs
        self.molecule_type = molecule_type
        self.source = source
        self.md5 = md5
        self.gc_content = gc_content
        self.cdss = DictList()
        self.taxonomy = taxonomy
        self.assembly_ref = assembly_ref
        self.taxon_ref = taxon_ref

    def add_cdss(self, cds_list: list):
        """

        :param cds_list:
        :return:
        """
        duplicates = list(filter(lambda o: o.id in self.cdss, cds_list))
        if len(duplicates) > 0:
            raise ValueError(
                f"unable to add cdss {duplicates} already present in the genome"
            )

        for f in cds_list:
            f._genome = self

        self.cdss += cds_list

    @staticmethod
    def from_kbase_data(kbase_data: dict, info=None, args=None):
        genome = KBaseGenome(
            kbase_data["id"],
            kbase_data["scientific_name"],
            kbase_data["domain"],
            kbase_data["genome_tiers"],
            kbase_data["feature_counts"],
            kbase_data["genetic_code"],
            kbase_data["dna_size"],
            kbase_data["num_contigs"],
            kbase_data["molecule_type"],
            kbase_data["source"],
            kbase_data["md5"],
            kbase_data["gc_content"],
            kbase_data.get("taxonomy", None),
            kbase_data.get("assembly_ref", None),
            kbase_data.get("taxon_ref", None),
            info,
            args,
        )
        features = [
            KBaseGenomeFeature.from_kbase_data(o) for o in kbase_data["features"]
        ]

        cdss = [KBaseGenomeCDS.from_kbase_data(o) for o in kbase_data["cdss"]]
        genome.add_features(features)
        genome.add_cdss(cdss)

        if "ontology_events" in kbase_data:
            # events = kbase_data['ontology_events']
            for feature_data in kbase_data["features"]:
                feature = genome.features.get_by_id(feature_data["id"])
                if "ontology_terms" in feature_data:
                    for term in feature_data["ontology_terms"]:
                        for value in feature_data["ontology_terms"][term]:
                            feature.add_ontology_term(term, value)

        return genome

    def _repr_html_(self):
        return """
        <table>
            <tr>
                <td><strong>ID</strong></td>
                <td>{id}</td>
            </tr><tr>
                <td><strong>Scientific Name</strong></td>
                <td>{scientific_name} ({domain})</td>
            </tr><tr>
                <td><strong>Taxonomy</strong></td>
                <td>{taxonomy}</td>
            </tr><tr>
                <td><strong>Sequence Data</strong></td>
                <td>Size: {dna_size}, Contigs: {num_contigs}, GC: {gc_content}</td>
            </tr><tr>
                <td><strong>CDS</strong></td>
                <td>{num_cdss}</td>
            </tr><tr>
                <td><strong>Features</strong></td>
                <td>{num_features}</td>
            </tr><tr>
                <td><strong>MD5</strong></td>
                <td>{md5}</td>
            </tr>
          </table>""".format(
            id=self.id,
            address="0x0%x" % id(self),
            scientific_name=self.scientific_name,
            domain=self.domain,
            taxonomy=self.taxonomy,
            gc_content=self.gc_content,
            dna_size=self.dna_size,
            num_contigs=self.num_contigs,
            num_cdss=len(self.cdss),
            num_features=len(self.features),
            md5=self.md5,
        )

    def to_kbase_data(self):
        raise Exception("Not implemented yet, sorry!")
