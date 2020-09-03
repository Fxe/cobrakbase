import math
import logging
from cobra.core import Reaction

logger = logging.getLogger(__name__)


class Biomass(Reaction):

    def __init__(self, data):
        #lower_bound, upper_bound = _get_reaction_constraints(data)
        #rxn_id = _build_rxn_id(data['id'])
        super().__init__(data['id'],
                         data['name'],
                         "",
                         0, 1000)

    def _to_json(self):
        #rev, max_flux, min_flux = self._get_rev_and_max_min_flux()
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
