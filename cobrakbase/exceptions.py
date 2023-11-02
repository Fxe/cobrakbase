class ObjectError(Exception):
    """Error in the construction of a base KBase object"""

    pass


class FeasibilityError(Exception):
    """Error in FBA formulation"""

    pass


class ShockException(Exception):
    """
    Error with Shock
    """

    pass
