import re
import hashlib
from modelseedpy.core.msgenome import MSFeature
from cobrakbase.core.utils import get_id_from_ref


class KBaseGenomeCDS(MSFeature):
    """
        Coding sequences are the sections of a feature's sequence that are translated
    to a protein (minus introns and UTRs).
    """

    def __init__(
        self, cds_id: str, protein_translation: str, dna_sequence: str, location: list
    ):
        """
                  parent_gene - string - gene (feature) from which this CDS comes from,
              including introns and UTRs that have been removed to create this CDS.
          parent_mrna - string - mRNA sequence from which this sequence is derived,
              including UTRs but not introns.
          note - string - TODO
          functions - list<string> - list of protein products or chemical
              processes that this sequence creates, facilitates, or influences.
          functional_descriptions - list<string> - TODO list of protein products or chemical
              processes that sequence creates, facilitates, or influences.
          ontology_terms - mapping<string, mapping<string, list<int>>> - a mapping
              of ontology source id (eg. "GO") to a mapping of term IDs (eg "GO:16209")
              to a list of indexes into the ontology_events data (found in the top
              level of the genome object). The index into an ontology event indicates
              what service and method created this term assignment.
          flags - list<string>  - (controlled vocab) fields from the genbank source. A
              common example is "pseudo" for pseudo-genes that do not encode proteins,
              which shows up as "/pseudo" in the genbank.
              Values can be: "pseudo", "ribosomal_slippage", "trans_splicing"
          warnings - list<string> - list of plain text warnings related to importing or constructing
              each feature
          inference_data - list<InferenceInfo> - TODO
          aliases - list<(string, string)> - alternative list of names or identifiers
              eg: [["gene", "thrA"], ["locus_tag", "b0002"]]
          db_xrefs - list<(string, string)> - Identifiers from other databases (database cross-references)
              The first string is the database name, the second is the database identifier.
              eg: [["ASAP", "ABE-0000006"], ["EcoGene", "EG11277"]]

        @optional Feature_id parent_gene;
        @optional mrna_id parent_mrna;
        @optional string note;
        @optional list<string> functions;
        @optional list<string> functional_descriptions;
        @optional mapping<string, mapping<string, list<int>>> ontology_terms;
        @optional list<string> flags;
        @optional list<string> warnings;
        @optional list<InferenceInfo> inference_data;
        @optional list<tuple<string, string>> aliases;
        @optional list<tuple<string, string>> db_xrefs;
        @optional string dna_sequence;

              @param cds_id: identifier of the coding sequence, such as "b0001_CDS_1"
              @param protein_translation: amino acid sequence that this CDS gets translated into
              @param dna_sequence: sequence of exons from the genome that constitute this protein encoding sequence
              @param location: locations from where this sequence originates in the original assembly.
              Each sub-sequence in the list constitutes a section of the resulting
              CDS. The first element in the tuple corresponds to the "contig_id",
              such as "NC_000913.3". The second element in the tuple is an index in
              the contig of where the sequence starts. The third element is either a
              plus or minus sign indicating whether it is on the 5' to 3' leading
              strand ("+") or on the 3' to 5' lagging strand ("-"). The last element
              is the length of the sub-sequence.
              For a location on the leading strand (denoted by "+"), the index is
              of the leftmost base, and the sequence extends to the right. For a
              location on the lagging strand (denoted by "-"), the index is of
              the rightmost base, and the sequence extends to the left.
              NOTE: the last element in each tuple is the *length* of each
              sub-sequence. If you have a location such as ("xyz", 100, "+", 50),
              then your sequence will go from index 100 to index 149 (this has a
              length of 50). It *does not* go from index 100 to index 150, as
              that would have a length of 51.
              Likewise, if you have the location ("xyz", 100, "-", 50), then the
              sequence extends from 100 down to 51, which has a length of 50
              bases. It does not go from index 100 to 50, as that would have a
              length of 51.
        """

        self.id = cds_id
        self.dna_sequence = dna_sequence
        self.location = location
        super().__init__(self, cds_id, protein_translation)

    @property
    def dna_md5(self):
        """
        @return: md5 string of the dna sequence
        """
        return hashlib.md5(self.dna_sequence.encode("utf-8")).hexdigest()

    @property
    def protein_md5(self):
        """
        @return: md5 string of the protein sequence that this CDS encodes
        """
        return hashlib.md5(self.seq.encode("utf-8")).hexdigest()

    @property
    def dna_sequence_length(self):
        """
        @return: length of the above
        """
        return len(self.dna_sequence)

    @property
    def protein_translation_length(self):
        """
        @return: length of the above
        """
        return len(self.seq)

    @staticmethod
    def from_kbase_data(kbase_data):
        protein_translation = kbase_data["protein_translation"]
        dna_sequence = kbase_data.get("dna_sequence")
        if protein_translation:
            protein_translation = protein_translation.upper()
        if dna_sequence:
            dna_sequence = dna_sequence.upper()
        result = KBaseGenomeCDS(
            kbase_data["id"], protein_translation, dna_sequence, kbase_data["location"]
        )
        return result

    def to_kbase_data(self):
        d = {
            "id": self.id,
            "dna_sequence_length": self.dna_sequence_length,
            "md5": self.dna_md5,
            "protein_translation": self.seq,
            "protein_translation_length": self.protein_translation_length,
            "protein_md5": self.protein_md5,
        }
        if self.dna_sequence:
            d["dna_sequence"] = self.dna_sequence
        return d


class KBaseGenomeFeature(MSFeature):
    def __init__(
        self,
        feature_id: str,
        protein_translation: str,
        dna_sequence: str,
        location,
        cdss: list,
        functions,
        aliases=None
    ):
        """
                Feature_id id;
        list<tuple<Contig_id, int, string, int>> location;
        int protein_translation_length;
        list<string> cdss;
        int dna_sequence_length;
        string md5;

        @optional list<string> functions;
        @optional list<string> functional_descriptions;
        @optional mapping<string, mapping<string, list<int>>> ontology_terms;
        @optional string note;
        @optional string protein_translation;
        @optional list<string> mrnas;
        @optional list<string> children;
        @optional list<string> flags;
        @optional list<string> warnings;
        @optional list<InferenceInfo> inference_data;
        @optional string dna_sequence;
        @optional list<tuple<string, string>> aliases;
        @optional list<tuple<string, string>> db_xrefs;


              @param feature_id:
              @param protein_translation:
              @param dna_sequence:
              @param location:
              @param cdss:
              @param functions:
        """

        self.dna_sequence = dna_sequence
        self.location = location
        self.cdss = cdss
        self.functions = set(functions)
        MSFeature.__init__(
            self, feature_id, protein_translation, "; ".join(self.functions), aliases
        )
        self.location = location

    # @property
    # def seq(self):
    #    return self.protein_translation

    @property
    def md5(self):
        return hashlib.md5(self.dna_sequence.encode("utf-8")).hexdigest()

    @property
    def dna_sequence_length(self):
        """
        @return: length of the above
        """
        return len(self.dna_sequence)

    @property
    def protein_translation_length(self):
        """
        @return: length of the above
        """
        return len(self.seq)

    @property
    def protein_translation(self):
        return self.seq

    def __str__(self):
        return self.id

    @staticmethod
    def split_annotation(annotation):
        split = set()
        for s in annotation:
            if s:
                for comp in re.split(" / | @ |; ", s):
                    split.add(comp)
            else:
                split.add(s)
        return split

    @staticmethod
    def split_function(function):
        split = set()
        if function:
            for comp in re.split(" / | @ |; ", function):
                split.add(comp)
        else:
            split.add(split)
        return split

    @staticmethod
    def extract_functions(data):
        functions = set()
        if "functions" in data:
            if type(data["functions"]) == str:
                return {data["functions"]}
            functions = set(data["functions"])
        elif "function" in data:
            functions = {data["function"]}
        return functions

    def _repr_html_(self):
        """
        taken from cobra.core.Model :)
        :return:
        """
        ots = ""
        for term in self.ontology_terms:
            ots += "<tr><td><strong>{}</strong></td><td>{}</td></tr>".format(
                term, "; ".join(self.ontology_terms[term])
            )
        return """
        <table>
            <tr>
                <td><strong>ID</strong></td>
                <td>{id}</td>
            </tr><tr>
                <td><strong>Memory address</strong></td>
                <td>{address}</td>
            </tr><tr>
                <td><strong>Ontology Terms</strong></td>
                <td>{terms}</td>
            </tr>{ots}<tr>
                <td><strong>DNA Sequence Length</strong></td>
                <td>{len_dna}</td>
            </tr><tr>
                <td><strong>Protein Translation Length</strong></td>
                <td>{len_protein}</td>
            </tr>
          </table>""".format(
            id=self.id,
            address="0x0%x" % id(self),
            functions="<br>".join(self.functions),
            len_dna=self.dna_sequence_length,
            len_protein=self.protein_translation_length,
            terms="; ".join(self.ontology_terms.keys()),
            ots=ots,
        )

    @staticmethod
    def from_kbase_data(kbase_data):
        functions = KBaseGenomeFeature.extract_functions(kbase_data)
        functions_split = KBaseGenomeFeature.split_annotation(functions)
        protein_translation = kbase_data["protein_translation"]
        dna_sequence = kbase_data["dna_sequence"]
        if protein_translation:
            protein_translation = protein_translation.upper()
        if dna_sequence:
            dna_sequence = dna_sequence.upper()
        feature = KBaseGenomeFeature(
            kbase_data["id"],
            protein_translation,
            dna_sequence,
            kbase_data["location"],
            kbase_data["cdss"],
            functions,
            kbase_data.get("aliases")
        )
        for f in functions_split:
            feature.add_ontology_term("RAST", f)
        return feature

    def to_kbase_data(self):
        d = {
            "id": self.id,
            "md5": self.md5,
            "cdss": self.cdss,
            "functions": list(self.functions),
            "location": self.location,
            "dna_sequence_length": self.dna_sequence_length,
            "protein_translation": self.seq,
            "protein_translation_length": self.protein_translation_length,
        }
        if self.dna_sequence:
            d["dna_sequence"] = self.dna_sequence
        return d
