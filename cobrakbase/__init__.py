def build_gene_id(str):
    if str.startswith("G_"):
        return str
    return "G_" + str

def build_cpd_id(str):
    if str.startswith("M_"):
        return str
    if str.startswith("M-"):
        return str
    return "M_" + str

def build_rxn_id(str):
    if str.startswith("R_"):
        return str
    if str.startswith("R-"):
        return str
    return "R_" + str

def get_id_from_ref(str):
    return str.split('/')[-1]

def get_genes(gpr):
    genes = set()
    for s in gpr:
        genes |= s
    return genes

def get_gpr_string(gpr):
    ors = []
    for ands in gpr:
        a = []
        for g in ands:
            a.append(g)
        ors.append(" and ".join(a))
    gpr_string = "(" + (") or (".join(ors)) + ")"
    if gpr_string.startswith("(") and gpr_string.endswith(")"):
        gpr_string = gpr_string[1:-1].strip()
    return gpr_string

def get_gpr(mr):
    gpr = []
    for mrp in mr['modelReactionProteins']:
        #print(mrp.keys())
        gpr_and = set()
        for mrps in mrp['modelReactionProteinSubunits']:
            #print(mrps.keys())
            for feature_ref in mrps['feature_refs']:
                gpr_and.add(get_id_from_ref(feature_ref))
        if len(gpr_and) > 0:
            gpr.append(gpr_and)
    return gpr