from cobrakbase.core.kbaseobject import KBaseObjectBase
from cobrakbase.core.utils import get_id_from_ref


class KBaseFBA(KBaseObjectBase):

    def get_reaction_variable_by_id(self, rxn_id):
        for v in self.data['FBAReactionVariables']:
            v_id = v['modelreaction_ref'].split('/')[-1]
            if rxn_id == v_id:
                return v
        return None

    @property
    def objective_value(self):
        return self.data['objectiveValue']
