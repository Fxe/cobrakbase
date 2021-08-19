import math
import copy
import logging
from cobra.core import Reaction
from modelseedpy.core.msmodel import get_direction_from_constraints

logger = logging.getLogger(__name__)


def get_for_rev_flux_from_bounds(lb, ub):
    rev_flux = 0
    for_flux = 0
    if lb > ub:
        return 0, 0
    if lb < 0:
        rev_flux = math.fabs(lb)
    if ub > 0:
        for_flux = ub
    return rev_flux, for_flux


def _get_gpr(data):
    gpr = []
    for mrp in data['modelReactionProteins']:
        #print(mrp.keys())
        gpr_and = []
        for mrps in mrp['modelReactionProteinSubunits']:
            gpr_or = []
            #print(mrps.keys())
            for feature_ref in mrps['feature_refs']:
                gpr_or.append(feature_ref.split('/')[-1])
            if len(gpr_or) > 0:
                gpr_and.append(gpr_or)
        if len(gpr_and) > 0:
            gpr.append(gpr_and)
    return gpr


def _get_gpr_string(gpr):
    ors = []
    for ands in gpr:
        a = []
        for orss in ands:
            if len(orss) == 1:
                a.append(orss[0])
            else:
                a.append("("+" or ".join(orss)+")")
        if len(a) == 1:
            ors.append(a[0])
        else:
            ors.append("("+" and ".join(a)+")")
    if len(ors) == 0:
        return ""
    elif len(ors) == 1:
        return ors[0]
    else:
        return "("+" or ".join(ors)+")"

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
    # clean this function !
    if 'maxrevflux' in data and 'maxforflux' in data:
        if data['maxrevflux'] == 1000000 and data['maxforflux'] == 1000000 and 'direction' in data:
            return _get_reaction_constraints_from_direction(data)

        return -1 * data['maxrevflux'], data['maxforflux']
    elif 'direction' in data:
        return _get_reaction_constraints_from_direction(data)
    else:
        logger.warning('unable to determine reversibility constraint assume reversible')
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

    def __init__(self, data, reaction_id=None,
                 name='', subsystem='', lower_bound=0.0, upper_bound=None, model=None):
        if model:
            self.model = model
        data_copy = copy.deepcopy(data)
        lower_bound, upper_bound = _get_reaction_constraints(data)
        rxn_id = _build_rxn_id(data['id'])
        super().__init__(rxn_id,
                         data['name'],
                         "",
                         lower_bound, upper_bound)
        
        logger.debug(rxn_id+":"+_get_gpr_string(_get_gpr(data)))
        self.gene_reaction_rule = _get_gpr_string(_get_gpr(data))

        for key in data_copy:
            if key not in COBRA_DATA:
                self.__dict__[key] = data_copy[key]

    @staticmethod
    def from_json(data):
        data_copy = copy.deepcopy(data)
        lower_bound, upper_bound = _get_reaction_constraints(data)
        rxn_id = _build_rxn_id(data['id'])
        return ModelReaction({}, rxn_id, data_copy['name'], "", lower_bound, upper_bound)

    @property
    def compartment(self):
        """
        single compartment return its element
        two compartments if e and c return c else return other than c
        (example e/c returns c, m/c returns m, p/c return c)
        """
        # FIXME: fix this, temporary hack this will break if not 0 index
        compartments = self.compartments
        if len(compartments) == 1:
            return list(compartments)[0]

        if 'e0' in compartments and 'c0' in compartments:
            return 'c0'
        elif len(compartments) == 2 and 'c0' in compartments:
            return list(compartments - {'c0'})[0]

        return 'c0'
    
    def _get_rev_and_max_min_flux(self):
        rev = get_direction_from_constraints(self.lower_bound, self.upper_bound)
        min_flux, max_flux = get_for_rev_flux_from_bounds(self.lower_bound, self.upper_bound)
        return rev, max_flux, min_flux

    def _to_json(self):
        rev, max_flux, min_flux = self._get_rev_and_max_min_flux()
        model_reaction_reagents = []
        s = self.metabolites
        for m in s:
            model_reaction_reagents.append({
                'modelcompound_ref': '~/modelcompounds/id/' + m.id,
                'coefficient': s[m]
            })

        model_reaction_proteins = []
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
            'modelReactionProteins': model_reaction_proteins,
            'modelReactionReagents': model_reaction_reagents,
            'modelcompartment_ref': '~/modelcompartments/id/' + self.compartment,
            'numerical_attributes': {},
            'probability': 0,
            'protons': 0,
            'reaction_ref': '~/template/reactions/id/' + self.id[:-1],
            'string_attributes': {}
        }
