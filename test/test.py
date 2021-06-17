from cobrakbase.core.kbasefba.fbamodel_reaction import get_for_rev_flux_from_bounds


def test_get_for_rev_flux_from_bounds():
    # TODO: copied from notebook fix this later
    print(get_for_rev_flux_from_bounds(-5, 5))
    print(get_for_rev_flux_from_bounds(0, 5))
    print(get_for_rev_flux_from_bounds(-5, 0))
    print(get_for_rev_flux_from_bounds(1, 5))
    print(get_for_rev_flux_from_bounds(-5, -1))
    print(get_for_rev_flux_from_bounds(0, 0))
    print(get_for_rev_flux_from_bounds(-5, -10))
