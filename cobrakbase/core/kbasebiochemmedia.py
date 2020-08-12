from cobrakbase.core.kbaseobject import KBaseObjectBase
from cobrakbase.core.utils import get_id_from_ref


class KBaseBiochemMedia(KBaseObjectBase):

    def get_media_constraints(self, cmp='e0'):
        """
        Parameters:
            cmp (str): compound suffix (model compartment)
        Returns:
            dict(str) -> (float,float): compound_ids mapped to lower/upper bound
        """
        media = {}
        for mediacompound in self.data['mediacompounds']:
            met_id = get_id_from_ref(mediacompound['compound_ref'])
            lb = -1 * mediacompound['maxFlux']
            ub = -1 * mediacompound['minFlux']
            if cmp is not None:
                met_id += '_' + cmp
            media[met_id] = (lb, ub)

        return media
