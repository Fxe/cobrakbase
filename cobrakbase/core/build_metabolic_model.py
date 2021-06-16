import logging
import modelseedpy
from modelseedpy.core.rast_client import RastClient
from cobrakbase.core.kbasefba.fbamodel_builder import FBAModelBuilder
from cobrakbase.core.kbasefba.fbamodel_reaction import ModelReaction
from cobrakbase.core.kbasefba.fbamodel_metabolite import ModelCompound

logger = logging.getLogger(__name__)


def NewModelTemplateReactionToReaction(template_reaction, gpr, genome, template, index='0'):
    reaction_compartment = 'c'
    proteins = []
    for complex_id in gpr:
        cpx = {
            'complex_ref': '~/template/complexes/name/' + complex_id,
            'modelReactionProteinSubunits': [],
            'note': '',
            'source': ''
        }
        for gene_id in gpr[complex_id]:
            cpx['modelReactionProteinSubunits'].append({
                'feature_refs': ['~/genome/features/id/' + gene_id],
                'note': '',
                'optionalSubunit': 0,
                'role': 'xxxxx',  # fix this
                'triggering': 1
            })
        proteins.append(cpx)

    model_reaction_data = {
        'id': "{}{}".format(template_reaction.id, index),
        'name': "{}_{}{}".format(template_reaction.name, reaction_compartment, index),
        'direction': template_reaction.direction,
        'aliases': [],
        'coverage': 3,
        'dblinks': {},
        'edits': {}, 'gapfill_data': {},
        'gene_count': 3,
        'maxforflux': 1000000,
        'maxrevflux': 1000000,
        'modelReactionProteins': proteins,
        'modelReactionReagents': [],
        'modelcompartment_ref': '~/modelcompartments/id/c0',
        'numerical_attributes': {}, 'string_attributes': {},
        'probability': 1,
        'protons': 0,
        'reaction_ref': '~/template/reactions/id/' + template_reaction.id,
    }

    metabolites = {}
    for o in template_reaction.templateReactionReagents:
        comp_compound = template_reaction.template.compcompounds.get_by_id(o['templatecompcompound_ref'].split('/')[-1])
        compound = template_reaction.template.compounds.get_by_id(comp_compound['templatecompound_ref'].split('/')[-1])
        cpd = ModelCompound(
            {
                'id': comp_compound.id + str(index),
                'modelcompartment_ref': comp_compound.templatecompartment_ref + str(index),
                'formula': compound.formula,
                'name': compound.name,
                'charge': comp_compound.charge
            })
        metabolites[cpd] = o['coefficient']
    reaction = ModelReaction(model_reaction_data)
    reaction.add_metabolites(metabolites)
    return reaction


def build_model_from_some_map(model_id, rxn_ids, genome, template, index='0', allow_all_non_grp_reactions=False):
    model_base = {
        'id': model_id,
        'name': model_id,
        'modelcompounds': [], 'modelreactions': [],
        '__VERSION__': 1,
        'attributes': {'auxotrophy': {}, 'fbas': {}, 'gene_count': 0, 'pathways': {}},
        'biomasses': [],
        'contig_coverages': {},
        'delete_biomasses': {},
        'deleted_reactions': {},
        'gapfilledcandidates': [], 'gapfillings': [], 'gapgens': [],
        'genome_ref': str(genome.info),
        'loops': [],
        'model_edits': [],
        'modelcompartments': [{'compartmentIndex': 0,
                               'compartment_ref': '~/template/compartments/id/c',
                               'id': 'c0',
                               'label': 'Cytosol_0',
                               'pH': 7,
                               'potential': 0},
                              {'compartmentIndex': 0,
                               'compartment_ref': '~/template/compartments/id/e',
                               'id': 'e0',
                               'label': 'Extracellular_0',
                               'pH': 7,
                               'potential': 0}],
        'other_genome_refs': [],
        'quantopts': [],
        'source': 'COBRA KBase',
        'source_id': 'COBRA KBase',
        'template_ref': str(template.info),
        'template_refs': [str(template.info)],
        'type': 'GenomeScale'
    }
    reactions = []
    for rxn_id in rxn_ids:
        template_reaction = template.reactions.get_by_id(rxn_id)
        model_reaction = NewModelTemplateReactionToReaction(template_reaction, rxn_ids[rxn_id], genome, template, index)
        reactions.append(model_reaction)

    b = FBAModelBuilder(model_base)
    cobra_model = b.build()
    cobra_model.add_reactions(reactions)

    reactions_no_gpr = []
    reactions_in_model = set(map(lambda x: x.id, cobra_model.reactions))
    metabolites_in_model = set(map(lambda x: x.id, cobra_model.metabolites))
    for rxn in template.reactions:
        if rxn.data['type'] == 'universal' or rxn.data['type'] == 'spontaneous':
            res = NewModelTemplateReactionToReaction(rxn, {}, genome, template)
            res_metabolite_ids = set(map(lambda x: x.id, set(res.metabolites)))
            if (len(metabolites_in_model & res_metabolite_ids) > 0 or allow_all_non_grp_reactions) and \
                    res.id not in reactions_in_model:
                reactions_no_gpr.append(res)
    cobra_model.add_reactions(reactions_no_gpr)

    return cobra_model


def build_metabolic_model(model_id, genome, template, index='0', allow_all_non_grp_reactions=False):
    rast = RastClient()

    p_features = []
    seqs = []
    for f in genome.features:
        if f.protein_translation and len(f.protein_translation) > 0:
            seqs.append(modelseedpy.core.msgenome.Sequence(f.id, f.protein_translation))
            p_features.append({
                'id': f.id,
                'protein_translation': f.protein_translation,
            })
    logger.info('seqs: %s', len(seqs))
    g = modelseedpy.core.msgenome.MSGenome()
    g.features += seqs
    logger.info('run rast...')
    res = rast.f(p_features)
    logger.info('run rast... [done]')

    search_name_to_genes, search_name_to_original = modelseedpy.core.rast_client.aux_rast_result(res, g)
    rxn_roles = modelseedpy.core.rast_client.aux_template(template)

    metabolic_reactions = {}
    genome_search_names = set(search_name_to_genes)
    for rxn_id in rxn_roles:
        sn_set = set(genome_search_names & rxn_roles[rxn_id])
        if len(sn_set) > 0:
            genes = set()
            for sn in sn_set:
                if sn in search_name_to_genes:
                    genes |= search_name_to_genes[sn]
            metabolic_reactions[rxn_id] = genes
            # metabolic_reactions.add(rxn_id)
            # print(rxn_id, genome_search_names & rxn_roles[rxn_id])
    logger.info('metabolic_reactions: %s', len(metabolic_reactions))

    # temporary hack until proper complexes from template
    metabolic_reactions_2 = {}
    cpx_random = 0
    for rxn_id in metabolic_reactions:
        metabolic_reactions_2[rxn_id] = {}
        for gene_id in metabolic_reactions[rxn_id]:
            metabolic_reactions_2[rxn_id]['complex' + str(cpx_random)] = {gene_id}
            cpx_random += 1

    cobra_model = build_model_from_some_map(model_id, metabolic_reactions_2, genome, template,
                                            index, allow_all_non_grp_reactions)
    return cobra_model
