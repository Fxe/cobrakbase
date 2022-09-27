from cobrakbase.core.kbasefba.newmodeltemplate import NewModelTemplate
from cobrakbase.core.kbasefba.newmodeltemplate_metabolite import NewModelTemplateCompound, NewModelTemplateCompCompound
from cobrakbase.core.kbasefba.newmodeltemplate_complex import NewModelTemplateRole, NewModelTemplateComplex
from cobrakbase.core.kbasefba.newmodeltemplate_reaction import NewModelTemplateReaction


def test_add_role1():
    role1 = NewModelTemplateRole('role1', 'A fine function for a gene')
    complex1 = NewModelTemplateComplex('complex1', 'A simple complex')
    complex1.add_role(NewModelTemplateRole('role1', 'A fine function for a gene'))

    assert id(list(complex1.roles)[0]) != id(role1)

    template = NewModelTemplate("test")
    template.add_complexes([complex1])

    assert id(list(template.complexes.complex1.roles)[0]) != id(role1)


def test_add_role2():
    role1 = NewModelTemplateRole('role1', 'A fine function for a gene')
    complex1 = NewModelTemplateComplex('complex1', 'A simple complex')
    complex1.add_role(NewModelTemplateRole('role1', 'A fine function for a gene'))

    assert id(list(complex1.roles)[0]) != id(role1)

    template = NewModelTemplate("test")
    template.add_roles([role1])
    template.add_complexes([complex1])

    assert id(list(template.complexes.complex1.roles)[0]) == id(role1)


def test_add_role3():
    role1 = NewModelTemplateRole('role1', 'A fine function for a gene')
    complex1 = NewModelTemplateComplex('complex1', 'A simple complex')
    complex1.add_role(role1)

    assert id(list(complex1.roles)[0]) == id(role1)

    template = NewModelTemplate("test")
    template.add_roles([role1])
    template.add_complexes([complex1])

    assert id(list(template.complexes.complex1.roles)[0]) == id(role1)


def test_add_role4():
    template = NewModelTemplate("test")

    role1 = NewModelTemplateRole('role1', 'A fine function for a gene')
    role2 = NewModelTemplateRole('role2', 'A fine sub unit A for a complex ABX')
    role3 = NewModelTemplateRole('role3', 'A fine sub unit B for a complex ABX')
    role4 = NewModelTemplateRole('role4', 'A not needed sub unit X for a complex ABX')

    template.add_roles([role1])

    complex1 = NewModelTemplateComplex('complex1', 'A simple complex')
    complex1.add_role(NewModelTemplateRole('role1', 'A fine function for a gene'))
    complex2 = NewModelTemplateComplex('complex2', 'A complex complex')
    complex2.add_role(role2)
    complex2.add_role(role3)
    complex2.add_role(role4, optional=True)

    template.add_complexes([complex1, complex2])

    assert len(template.roles) == 4
    assert len(template.complexes) == 2
    assert len(template.complexes.complex1.roles) == 1
    assert len(template.complexes.complex2.roles) == 3


def test_add_reaction1():
    cpd_nad = NewModelTemplateCompCompound('cpd00003_c', 0, 'c', 'cpd00003')
    cpd_coa = NewModelTemplateCompCompound('cpd00010_c', 0, 'c', 'cpd00010')
    cpd_pyr = NewModelTemplateCompCompound('cpd00020_c', 0, 'c', 'cpd00020')
    cpd_nadh = NewModelTemplateCompCompound('cpd00004_c', 0, 'c', 'cpd00004')
    cpd_co2 = NewModelTemplateCompCompound('cpd00011_c', 0, 'c', 'cpd00011')
    cpd_accoa = NewModelTemplateCompCompound('cpd00022_c', 0, 'c', 'cpd00022')
    rxn1 = NewModelTemplateReaction('rxn1', 'rxn1')
    rxn1.add_metabolites({
        cpd_nad: -1,
        cpd_coa: -1,
        cpd_pyr: -1,
        cpd_nadh: 1,
        cpd_accoa: 1,
        cpd_co2: 1
    })
    rxn1
