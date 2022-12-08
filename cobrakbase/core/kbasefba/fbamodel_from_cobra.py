import logging
from cobrakbase.core.kbasefba.fbamodel_builder import FBAModelBuilder
from cobrakbase.core.kbasefba.fbamodel_metabolite import ModelCompound
from cobrakbase.core.kbasefba.fbamodel_reaction import ModelReaction
from cobrakbase.core.kbasefba.fbamodel_biomass import Biomass

logger = logging.getLogger(__name__)


class CobraModelConverter:
    def __init__(self, model, genome=None, template=None):
        self.model = model
        self.model_id = model.id
        self.template = template
        self.genome = genome
        self.drain_exclude_set = {"rxn13782", "rxn13783", "rxn13784"}
        self.extract_seed_it_from_identifier = (
            False  # Detect seed id from identifier if annotation is missing
        )

    @staticmethod
    def convert_reaction_to_biomass(reaction):
        reaction_biomass = Biomass(reaction.id, reaction.name)
        reaction_biomass.add_metabolites(reaction.metabolites)
        reaction_biomass.notes = reaction.notes
        reaction_biomass.annotation = reaction.annotation
        return reaction_biomass

    @staticmethod
    def reaction_is_biomass(reaction):
        """
        detect biomass reaction from SBO term SBO:0000629
        """
        return (
            type(reaction) == Biomass
            or "sbo" in reaction.annotation
            and reaction.annotation["sbo"] == "SBO:0000629"
        )

    @staticmethod
    def get_seed_id(reaction, detect_from_id=False):
        if "seed.reaction" in reaction.annotation:
            return reaction.annotation["seed.reaction"]
        if detect_from_id:
            if reaction.id.startswith("rxn") and reaction.id[3:8].isdigit():
                return reaction.id[:8]
        return None

    @staticmethod
    def reaction_is_drain(reaction, detect_from_id=False, exclude=None):
        if exclude is None:
            exclude = {}
        """
        assume reactions of size 1 as drain reactions
        if annotated with sbo SBO:0000176 overrides drain check
        """
        if exclude is None:
            exclude = set()
        if "sbo" in reaction.annotation and reaction.annotation["sbo"] == "SBO:0000176":
            return False
        if "sbo" in reaction.annotation and reaction.annotation["sbo"] in {
            "SBO:0000632",
            "SBO:0000628",
        }:
            return True
        return (
            CobraModelConverter.get_seed_id(reaction, detect_from_id) not in exclude
            and len(reaction.metabolites) == 1
        )

    @staticmethod
    def reaction_is_exchange(reaction, detect_from_id=False, exclude=None):
        if exclude is None:
            exclude = {}
        """
        assume reactions of size 1 as drain reactions
        if annotated with sbo SBO:0000176 overrides drain check
        """
        if "sbo" in reaction.annotation and reaction.annotation["sbo"] == "SBO:0000176":
            return False
        if "sbo" in reaction.annotation and reaction.annotation["sbo"] == "SBO:0000627":
            return True
        compartments = reaction.compartments
        return (
            CobraModelConverter.get_seed_id(reaction, detect_from_id) not in exclude
            and len(reaction.metabolites) == 1
            and len(compartments) == 1
            and (list(compartments)[0] == "e0" or list(compartments)[0] == "e")
        )

    def get_template_ref(self):
        if self.template:
            return str(self.template.info)
        return ""

    def get_genome_ref(self):
        if self.genome:
            return str(self.genome.info)
        return None

    @property
    def metabolic_reactions(self):
        for reaction in self.model.reactions:
            if not self.reaction_is_biomass(reaction) and not self.reaction_is_drain(
                reaction, self.extract_seed_it_from_identifier, self.drain_exclude_set
            ):
                yield reaction

    @property
    def biomass_reactions(self):
        for reaction in self.model.reactions:
            if CobraModelConverter.reaction_is_biomass(reaction):
                yield reaction

    def build(self):
        model_compartments = []
        for cmp_id in self.model.compartments:
            # TODO split cmp_id to extract index and compartment_ref no index assume 0
            model_compartments.append(
                {
                    "compartmentIndex": 0,
                    "id": cmp_id,
                    "label": self.model.compartments[cmp_id],
                    "compartment_ref": "~/template/compartments/id/" + cmp_id[0],
                    "pH": 7,
                    "potential": 0,
                }
            )

        model_compounds = {}
        for m in self.model.metabolites:
            model_compound = ModelCompound(
                m.id, m.formula, m.name, m.charge, m.compartment
            )
            model_compound.notes = m.notes
            model_compound.annotation = m.annotation
            if model_compound.id not in model_compounds:
                model_compounds[model_compound.id] = model_compound
            else:
                logger.warning(f"duplicate metabolite {model_compound.id}")

        model_reactions = []
        for r in self.metabolic_reactions:
            model_reaction = ModelReaction(
                r.id,
                r.name,
                r.subsystem,
                r.lower_bound,
                r.upper_bound,
                imported_gpr=r.gene_reaction_rule,
            )
            model_reaction.notes = r.notes
            model_reaction.annotation = r.annotation
            model_reaction.gene_reaction_rule = r.gene_reaction_rule
            model_reaction.add_metabolites(
                dict([(model_compounds[c.id], v) for (c, v) in r.metabolites.items()])
            )
            model_reactions.append(model_reaction)

        model_biomass = {}
        for r in self.biomass_reactions:
            reaction_biomass = self.convert_reaction_to_biomass(r)
            model_biomass[reaction_biomass.id] = reaction_biomass
            """
            
            biomass_compounds = []
            metabolites = r.metabolites
            for m in metabolites:
                biomass_compounds.append({
                    'coefficient': metabolites[m],
                    'edits': {},
                    'gapfill_data': {},
                    'modelcompound_ref': '~/modelcompounds/id/' + m.id
                })
            biomass = {
                'id': r.id,
                'name': r.name,
                'biomasscompounds': biomass_compounds,
                'dna': 0,
                'rna': 0,
                'protein': 0,
                'cellwall': 0,
                'cofactor': 0,
                'energy': 0,
                'lipid': 0,
                'other': 0,
                'edits': {},
                'deleted_compounds': {},
                'removedcompounds': []
              }
            model_biomass.append(biomass)
            """

        if len(model_biomass) == 0:
            logger.warning("no biomass reaction provided or detected")

        model_base = {
            "__VERSION__": 1,
            "id": self.model_id,
            "source_id": self.model_id,
            "name": self.model_id,
            "source": "ModelSEEDpy",
            "modelcompartments": model_compartments,
            "modelcompounds": [o._to_json() for o in model_compounds.values()],
            "modelreactions": [],
            # 'modelreactions': [o._to_json() for o in model_reactions],
            "biomasses": [o._to_json() for o in model_biomass.values()],
            "attributes": {
                "auxotrophy": {},
                "fbas": {},
                "gene_count": 0,
                "pathways": {},
            },
            "contig_coverages": {},
            "delete_biomasses": {},
            "deleted_reactions": {},
            "gapfilledcandidates": [],
            "gapfillings": [],
            "gapgens": [],
            "genome_ref": "",
            "loops": [],
            "model_edits": [],
            "other_genome_refs": [],
            "quantopts": [],
            "template_ref": self.get_template_ref(),
            "template_refs": [self.get_template_ref()],
            "type": "GenomeScale",
        }
        if self.get_genome_ref():
            model_base["genome_ref"] = self.get_genome_ref()

        cobra_model = FBAModelBuilder(model_base).build()
        cobra_model.genome = self.genome
        cobra_model.name = self.model.name
        cobra_model.notes = self.model.notes
        cobra_model.annotation = self.model.annotation
        cobra_model.add_groups(self.model.groups)
        #
        cobra_model.add_reactions(model_reactions)
        return cobra_model
