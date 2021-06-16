import copy
from cobrakbase.core.kbasefba.fbamodel_builder import FBAModelBuilder
from cobrakbase.kbase_object_info import KBaseObjectInfo
from cobrakbase.core.fba_utilities import KBaseFBAUtilities


def gapfill(model, template=None,
            media=None, kbmodel=None, kbase_api=None):
    utilities = KBaseFBAUtilities(model, kbmodel, kbase_api, media=media,
                                  default_uptake=100,
                                  default_excretion=100,
                                  blacklist=[], template=template)
    if media:
        utilities.cobramodel.medium = media
    utilities.default_uptake = 0
    penalties = utilities.build_model_extended_for_gapfilling(1, [], [], 2, {})
    utilities.set_objective_from_target_reaction('bio1', 1)
    utilities.convert_objective_to_constraint(0.1, None)
    utilities.create_minimal_reaction_objective(penalties, default_penalty=0)
    gapfilling_solution = model.optimize()
    print('gapfilling_solution.objective_value', gapfilling_solution.objective_value)
    output_1 = utilities.compute_gapfilled_solution(penalties)
    flux_values = utilities.binary_check_gapfilling_solution(penalties, 1)
    output_2 = utilities.compute_gapfilled_solution(penalties, flux_values)
    return output_1, output_2


def insert_gf(kbmodel, output_2, template_json):
    model_json_gf = copy.deepcopy(kbmodel)
    for rxn_id in output_2['reversed']:
        list(filter(lambda x: x['id'] == rxn_id, model_json_gf['modelreactions']))[0]['direction'] = output_2['reversed'][rxn_id]
    for rxn_id in output_2['new']:
        rxn = list(filter(lambda x: x['id'] == rxn_id[:-1], template_json['reactions']))[0]
        model_reaction_reagents = []
        for trr in rxn['templateReactionReagents']:
            cc = list(filter(lambda x: x['id'] == trr['templatecompcompound_ref'].split('/')[-1], template_json['compcompounds']))[0]
            modelcompounds = list(filter(lambda x: x['id'] == cc['id'] + '0', model_json_gf['modelcompounds']))
            if len(modelcompounds) == 0:
                tc = list(filter(lambda x: x['id'] == cc['templatecompound_ref'].split('/')[-1], template_json['compounds']))[0]
                cmp = cc['templatecompartment_ref'].split('/')[-1]
                model_json_gf['modelcompounds'].append({
                    'aliases': [],
                    'charge': -1,
                    'compound_ref': '~/template/compounds/id/' + tc['id'],
                    'dblinks': {},
                    'formula': tc['formula'],
                    'id': tc['id'] + '_' + cmp + '0',
                    'inchikey': '',
                    'modelcompartment_ref': '~/modelcompartments/id/' + cmp + '0',
                    'name': tc['name'],
                    'numerical_attributes': {},
                    'smiles': '',
                    'string_attributes': {}})
                modelcompounds = list(filter(lambda x: x['id'] == cc['id'] + '0', model_json_gf['modelcompounds']))
            if len(modelcompounds) == 1:
                mrr = {'coefficient': trr['coefficient'], 'modelcompound_ref': '~/modelcompounds/id/' + modelcompounds[0]['id']}
                model_reaction_reagents.append(mrr)
            else:
                print('!! need add', cc['id'] + '0')
        model_rxn = {
            'aliases': [],
            'coverage': 4,
            'dblinks': {},
            'direction': output_2['new'][rxn_id],
            'edits': {},
            'gapfill_data': {},
            'gene_count': 0,
            'id': rxn_id,
            'maxforflux': 1000000,
            'maxrevflux': 1000000,
            'modelReactionProteins': [],
            'modelReactionReagents': model_reaction_reagents,
            'modelcompartment_ref': '~/modelcompartments/id/c0',
            'name': rxn['name'],
            'numerical_attributes': {},
            'probability': 1,
            'protons': 0,
            'reaction_ref': '~/template/reactions/id/' + rxn['id'],
            'string_attributes': {}}
        model_json_gf['modelreactions'].append(model_rxn)
    oi = KBaseObjectInfo(object_type='KBaseFBA.FBAModel-12.0')
    model_gf = FBAModelBuilder(model_json_gf, oi).with_sink('cpd11416_c0') \
                                                 .with_sink('cpd02701_c0') \
                                                 .with_sink('cpd15302_c0') \
                                                 .build()
    return model_gf


def combine(outputs):
    res = {
        'reversed': {},
        'new': {}
    }
    for o in outputs:
        for rxn_id in o['reversed']:
            if rxn_id not in res['reversed']:
                res['reversed'][rxn_id] = o['reversed'][rxn_id]
            else:
                prev = res['reversed'][rxn_id]
                if prev != o['reversed'][rxn_id]:
                    res['reversed'][rxn_id] = '='
        for rxn_id in o['new']:
            if rxn_id not in res['new']:
                res['new'][rxn_id] = o['new'][rxn_id]
            else:
                prev = res['new'][rxn_id]
                if prev != o['new'][rxn_id]:
                    res['new'][rxn_id] = '='
    return res
