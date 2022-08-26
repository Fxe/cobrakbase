import logging
from cobrakbase.core.kbasefba.fbamodel_builder import FBAModelBuilder
from cobrakbase.core.kbasefba.fbamodel_metabolite import ModelCompound
from cobrakbase.core.kbasefba.fbamodel_reaction import ModelReaction, get_for_rev_flux_from_bounds
from modelseedpy.core.msmodel import get_direction_from_constraints
from cobrakbase.core.kbasefba.fbamodel_biomass import Biomass

logger = logging.getLogger(__name__)


class CobraModelConverter:

    def __init__(self, model, genome=None, template=None):
        self.model = model
        self.model_id = model.id
        self.template = template
        self.genome = genome

    @staticmethod
    def reaction_is_biomass(reaction):
        """
        detect biomass reaction from SBO term SBO:0000629
        """
        return type(reaction) == Biomass or \
            'sbo' in reaction.annotation and reaction.annotation['sbo'] == "SBO:0000629"

    @staticmethod
    def reaction_is_drain(reaction):
        """
        assume reactions of size 1 as drain reactions
        if annotated with sbo SBO:0000176 overrides drain check
        """
        if 'sbo' in reaction.annotation and reaction.annotation['sbo'] == "SBO:0000176":
            return False
        return len(reaction.metabolites) == 1

    def get_template_ref(self):
        if self.template:
            return str(self.template.info)
        return ''

    def get_genome_ref(self):
        if self.genome:
            return str(self.genome.info)
        return None

    @property
    def metabolic_reactions(self):
        for reaction in self.model.reactions:
            if not self.reaction_is_biomass(reaction) and not self.reaction_is_drain(reaction):
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
            model_compartments.append({
                'compartmentIndex': 0,
                'id': cmp_id,
                'label': self.model.compartments[cmp_id],
                'compartment_ref': '~/template/compartments/id/' + cmp_id[0],
                'pH': 7,
                'potential': 0
            })

        model_compounds = []
        for m in self.model.metabolites:
            model_compound = ModelCompound({
                'id': m.id,
                'modelcompartment_ref': '~/modelcompartments/id/' + m.compartment,
                'formula': m.formula,
                'name': m.name,
                'charge': m.charge
            })
            model_compounds.append(model_compound._to_json())

        model_reactions = []
        for r in self.metabolic_reactions:
            direction = get_direction_from_constraints(r.lower_bound, r.upper_bound)
            if direction == '?':
                logger.warning('invalid bounds assume reversible %s %s', r.lower_bound, r.upper_bound)
                direction = '='
            max_rev_flux, max_for_flux = get_for_rev_flux_from_bounds(r.lower_bound, r.upper_bound)
            proteins = []
            model_reaction_data = {
                'id': r.id,
                'name': r.name,
                'direction': direction,
                'aliases': [],
                'coverage': 3,
                'dblinks': {},
                'edits': {}, 'gapfill_data': {},
                'gene_count': 0,
                'maxrevflux': max_rev_flux,
                'maxforflux': max_for_flux,
                'modelReactionProteins': proteins,
                'modelReactionReagents': [],
                'modelcompartment_ref': '~/modelcompartments/id/c0',
                'numerical_attributes': {}, 'string_attributes': {},
                'probability': 1,
                'protons': 0,
                'reaction_ref': '~/template/reactions/id/' + r.id[:-1],
            }
            model_reaction = ModelReaction(model_reaction_data)
            model_reaction.add_metabolites(r.metabolites)
            model_reactions.append(model_reaction._to_json())

        model_biomass = []
        for r in self.biomass_reactions:
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
                'dna': 0.031,
                'rna': 0.21,
                'protein': 0.563,
                'cellwall': 0.177,
                'cofactor': 0.039,
                'energy': 40,
                'lipid': 0.093,
                'other': 0,
                'edits': {},
                'deleted_compounds': {},
                'removedcompounds': []
              }
            model_biomass.append(biomass)

        if len(model_biomass) == 0:
            logger.warning('no biomass reaction provided or detected')

        model_base = {
            '__VERSION__': 1,
            'id': self.model_id,
            'source_id': self.model_id,
            'name': self.model_id,
            'source': 'ModelSEEDpy',
            'modelcompartments': model_compartments,
            'modelcompounds': model_compounds,
            'modelreactions': model_reactions,
            'biomasses': model_biomass,
            'attributes': {'auxotrophy': {}, 'fbas': {}, 'gene_count': 0, 'pathways': {}},
            'contig_coverages': {},
            'delete_biomasses': {},
            'deleted_reactions': {},
            'gapfilledcandidates': [], 'gapfillings': [], 'gapgens': [],
            'loops': [],
            'model_edits': [],
            'other_genome_refs': [],
            'quantopts': [],
            'template_ref': self.get_template_ref(),
            'template_refs': [self.get_template_ref()],
            'type': 'GenomeScale'
        }
        if self.get_genome_ref():
            model_base['genome_ref'] = self.get_genome_ref()

        cobra_model = FBAModelBuilder(model_base).build()
        return model_base, cobra_model
