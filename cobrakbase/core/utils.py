import logging
import math
from itertools import permutations

logger = logging.getLogger(__name__)


def get_cmp_token(cmps):
    if len(cmps) == 1:
        return list(cmps)[0]
    if len(cmps) == 2:
        if 'b' in cmps and 'e' in cmps:
            return 'b'
        if 'e' in cmps and 'c' in cmps:
            return 'c'
        if 'c' in cmps:
            return list(filter(lambda x : not x == 'c', cmps))[0]
    #print('!@??!', cmps)
    return None


def get_compartment_config_single(model_cstoichiometry, rxn_cstoichiometry):
    result = None

    cmps = list(set(map(lambda x: x[1], model_cstoichiometry)))
    cmps_replace = list(set(map(lambda x: x[1], rxn_cstoichiometry)))
    for perm in list(permutations(cmps)):
        cmp_config = {}
        for i in range(len(cmps)):
            cmp_config[cmps_replace[i]] = perm[i]
        test = dict(map(lambda x: ((x[0][0], cmp_config[x[0][1]]), x[1]), rxn_cstoichiometry.items()))
        match = test == model_cstoichiometry
        logger.debug('%s => %s', cmp_config, match)
        if match:
            result = cmp_config
    return result


def get_compartment_config_matches(model_cstoichiometry, rxn_cstoichiometry):
    result = set()

    cmps = list(set(map(lambda x: x[1], model_cstoichiometry)))
    cmps_replace = list(set(map(lambda x: x[1], rxn_cstoichiometry)))
    if not len(cmps) == len(cmps_replace):
        logger.warning('compartments size do not match')
        return None
    for perm in list(permutations(cmps)):
        cmp_config = {}
        for i in range(len(cmps)):
            cmp_config[cmps_replace[i]] = perm[i]
        test = dict(map(lambda x: ((x[0][0], cmp_config[x[0][1]]), x[1]), rxn_cstoichiometry.items()))
        match = test == model_cstoichiometry

        logger.debug("M  %s", model_cstoichiometry)
        logger.debug("T  %s", test)

        logger.debug('%s => %s', cmp_config, match)
        if match:
            result.add(tuple(sorted(cmp_config.items())))
        # Test reverse stoichiometry
        test = dict(map(lambda x: (x[0], -1 * x[1]), test.items()))
        logger.debug("T' %s", test)
        match = test == model_cstoichiometry
        if match:
            result.add(tuple(sorted(cmp_config.items())))
    return result


def multiply(s, v):
    s_ = {}
    for i in s:
        s_[i] = v * s[i]
    return s_


def get_lower(s):
    return sorted(list(s))[0]


def get_locked(compartment_config):
    #print('get_locked', compartment_config)
    locked = {}
    for socket in compartment_config:
        if len(compartment_config[socket]) == 1:
            locked[socket] = compartment_config[socket].pop()
    return locked


def get_compartment_config(model_reaction, seed_reaction, locked = {}, depth = 0):
    model_reaction_reagents = model_reaction['modelReactionReagents']
    stoichiometry = seed_reaction['stoichiometry']
    #print('locked', locked)
    #print(stoichiometry)
    #print(model_reaction)
    
    compartment_config = {}
    for socket in locked:
        compartment_config[socket] = set([locked[socket]])
    all_compartments = set()
    #print(depth, 'initial', compartment_config)
    for p in stoichiometry.split(';'):
        o = p.split(':')
        #cmp = o[]
        value = float(o[0])
        compound_id = o[1]
        compartment_socket = int(o[2])
        if not compartment_socket in locked:
            if not compartment_socket in compartment_config:
                compartment_config[compartment_socket] = set()
            #print(depth, 'match socket', compartment_socket)
            for o in model_reaction_reagents:
                if compound_id in o['modelcompound_ref']:
                    cmp = o['modelcompound_ref'].split('_')[-1]
                    #print(depth, cmp, locked.values())
                    if not cmp in locked.values():
                        compartment_config[compartment_socket].add(cmp)
                    all_compartments.add(cmp)
    
    #print(depth, 'match result', compartment_config)

    
    all_compartments = sorted(list(all_compartments))
    
    if len(all_compartments) > 1:
        for socket in compartment_config:
            if len(compartment_config[socket]) > 1:
                compartment_config[socket] = set([get_lower(compartment_config[socket])])
                break
    
    l = get_locked(compartment_config)
    
    #print(depth, 'locked', l)
    
    if depth > 10:
        print('unable to detect valid configuration')
        return None
    if not l == locked:
        return get_compartment_config(model_reaction, seed_reaction, locked = l, depth = depth + 1)
    
    compartment_config = locked
    #print('yes!', compartment_config)
    
    for socket in compartment_config:
        if len(compartment_config[socket]) == 1:
            compartment_config[socket] = compartment_config[socket].pop()
    
    valid = True
    for socket in compartment_config:
        if not isinstance(compartment_config[socket], str):
            valid = False
            
    #print('valid', valid)
    if valid:
        return compartment_config
    
    return None


def get_reaction_compartment2(compartment_config):
    cmps = set(compartment_config.values())
    if not cmps == None:
        if len(cmps) == 1:
            return cmps.pop()
        elif 'c0' in cmps and len(cmps) == 2:
            cmps.remove('c0')
            return cmps.pop()
        print('fail', cmps)
    else:
        return None
    return "z0"


def get_bounds(r):
    maxrevflux = r['maxrevflux']
    maxforflux = r['maxforflux']
    direction = '='
    if maxrevflux == 0 and maxforflux > 0:
        direction = '>'
    elif maxrevflux > 0 and maxforflux == 0:
        direction = '<'
    elif maxrevflux == 0 and maxforflux == 0:
        direction = '0'
        
    return maxrevflux, maxforflux, direction


def seed_coefficients_to_string(coeff_list, op = '<=>'):
    lhs = []
    rhs = []
    pair_to_str = lambda v, id : id if math.fabs(v) == 1 else str(math.fabs(v)) + ' ' + id
    for o in coeff_list:
        cpd_id = o['modelcompound_ref'].split('/')[-1]
        value = o['coefficient']
        if value > 0:
            rhs.append(pair_to_str(value, cpd_id))
        elif value < 0:
            lhs.append(pair_to_str(value, cpd_id))
        else:
            logger.warning("zero value found: %s", o)
    return "{} {} {}".format(' + '.join(lhs), op, ' + '.join(rhs))


def print_stoich(stoich, eq="<=>"):
    l = {}
    r = {}
    for o in stoich:
        v = stoich[o]
        v_text = ""
        if not 1 == math.fabs(v):
            v_text = str(math.fabs(v)) + " "
        if v < 0:
            l[o] = v_text
        elif v > 0:
            r[o] = v_text
        else:
            print('warn: found zero value stoich', stoich)
            
    l_text = []
    r_text = []
    for i in l:
        l_text.append(l[i] + i)
    for i in r:
        r_text.append(r[i] + i)
    #print(l_text, r_text)
    return ' + '.join(l_text) + " " + eq + " " + ' + '.join(r_text)


def get_str(k, def_value, d):
    if k in d:
        if d[k] == None:
            return def_value
        return str(d[k])
    return def_value


def get_int(k, def_value, d):
    if k in d:
        if d[k] == None:
            return def_value
        return int(d[k])
    return def_value


def get_id_from_ref(str, stok='/'):
    return str.split(stok)[-1]