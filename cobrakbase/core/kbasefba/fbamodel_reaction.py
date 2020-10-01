import math
import copy
import logging
from cobra.core import Reaction

logger = logging.getLogger(__name__)


def _get_gpr(data):
    gpr = []
    for mrp in data['modelReactionProteins']:
        #print(mrp.keys())
        gpr_and = set()
        for mrps in mrp['modelReactionProteinSubunits']:
            #print(mrps.keys())
            for feature_ref in mrps['feature_refs']:
                gpr_and.add(feature_ref.split('/')[-1])
        if len(gpr_and) > 0:
            gpr.append(gpr_and)
    return gpr


def _get_gpr_string(gpr):
    ors = []
    for ands in gpr:
        a = []
        for g in ands:
            a.append(g)
        ors.append(" and ".join(a))
    gpr_string = "(" + (") or (".join(ors)) + ")"
    if gpr_string == "()":
        return ""
    #if gpr_string.startswith("(") and gpr_string.endswith(")"):
    #    gpr_string = gpr_string[1:-1].strip()
    return gpr_string


def _get_reaction_constraints_from_direction(data):
    if 'direction' in data:
        if data['direction'] == '>':
            return 0, 1000
        elif data['direction'] == '<':
            return -1000, 0
        else:
            return -1000, 1000
    return None, None


def _get_reaction_constraints(data):
    #clean this function !
    if 'maxrevflux' in data and 'maxforflux' in data:
        if data['maxrevflux'] == 1000000 and data['maxforflux'] == 1000000 and 'direction' in data:
            return _get_reaction_constraints_from_direction(data)

        return -1 * data['maxrevflux'], data['maxforflux']
    return -1000, 1000


def _build_rxn_id(s):
    if s.startswith("R_"):
        s = s[2:]
    elif s.startswith("R-"):
        s = s[2:]
    str_fix = s
    if '-' in str_fix:
        str_fix = str_fix.replace('-', '__DASH__')
    if not s == str_fix:
        logger.debug('[Reaction] rename: [%s] -> [%s]', s, str_fix)
    return str_fix


COBRA_DATA = ['id', 'name',
              'direction', 'maxrevflux', 'maxforflux',
              'modelReactionReagents']


class ModelReaction(Reaction):

    def __init__(self, data):
        data_copy = copy.deepcopy(data)
        lower_bound, upper_bound = _get_reaction_constraints(data)
        rxn_id = _build_rxn_id(data['id'])
        super().__init__(rxn_id,
                         data['name'],
                         "",
                         lower_bound, upper_bound)

        self.gene_reaction_rule = _get_gpr_string(_get_gpr(data))

        for key in data_copy:
            if key not in COBRA_DATA:
                self.__dict__[key] = data_copy[key]

    @property
    def compartment(self):
        return 'c0'
    
    def _get_rev_and_max_min_flux(self):
        rev = '='
        min_flux = math.fabs(self.lower_bound)
        max_flux = self.upper_bound
        return rev, max_flux, min_flux

    def _to_json(self):
        rev, max_flux, min_flux = self._get_rev_and_max_min_flux()
        return {
            'id': self.id,
            'name': self.name,
            'direction': rev,
            'maxforflux': max_flux,
            'maxrevflux': min_flux,
            'aliases': [],
            'dblinks': {},
            'edits': {},
            'gapfill_data': {},
            'modelReactionProteins': [],
            'modelReactionReagents': [],
            'modelcompartment_ref': '~/modelcompartments/id/c0',
            'numerical_attributes': {},
            'probability': 0,
            'protons': 0,
            'reaction_ref': '~/template/reactions/id/rxn02201_c',
            'string_attributes': {}
        }
