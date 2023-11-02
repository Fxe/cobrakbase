from cobrakbase.core.kbaseobject import KBaseObject
from cobrakbase.kbase_object_info import KBaseObjectInfo


class Media(KBaseObject):

    OBJECT_TYPE = "KBaseBiochem.Media"

    def __init__(self, data=None, info=None, args=None):
        if info is None:
            info = KBaseObjectInfo(object_type=Media.OBJECT_TYPE)
        super().__init__(data, info, args)

    def get_media_constraints(self, cmp="e0"):
        """
        Parameters:
            cmp (str): compound suffix (model compartment)
        Returns:
            dict(str) -> (float,float): compound_ids mapped to lower/upper bound
        """
        media = {}
        for mediacompound in self.data["mediacompounds"]:
            met_id = mediacompound["compound_ref"].split("/")[-1]
            lb = -1 * mediacompound["maxFlux"]
            ub = -1 * mediacompound["minFlux"]
            if cmp is not None:
                met_id += "_" + cmp
            media[met_id] = (lb, ub)

        return media
