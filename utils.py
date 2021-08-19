from itertools import chain, combinations


def _all_permutations(iterable):
    "all_permutation([0,1,2]) --> () (0,) (1,) (2,) (0,1) (0,2) (1,2) (0,1,2)"
    s = list(iterable)
    return list(chain.from_iterable(combinations(s, r) for r in range(len(s) + 1)))


def feasible_permutations(players_number, rt_players):
    set_players = []

    if rt_players is None:
        # one half rt and the other half nrt
        rt_players = round((players_number - 1) / 2)
    # assign type to players
    for i in range(players_number):
        # valid only for SPs
        # SPs NRT
        if i != 0 and rt_players > 0:
            set_players.append((i, "rt"))
            rt_players -= 1
        # SPs NRT
        elif i != 0:
            set_players.append((i, "nrt"))
        # NO
        else:
            set_players.append((i, "NO"))

    perms = _all_permutations(set_players)

    return perms

    # we can provide the number of config to try
    # inputs: type of slots, it can be seconds or minutes
    # realistic time horizon of a cpu


def generate_configs(max_config_number=23, type_slot='min', years_horizon=3):
    # available time horizons
    configurations = []
    one_year_minutes = 525600
    one_year_seconds = 3.154e+7
    T_horizon_avail = []
    if type_slot == "sec":
        t = one_year_seconds
    elif type_slot == "min":
        t = one_year_minutes
    for i in range(years_horizon):
        T_horizon_avail.append(t * (i + 1))
    # available cpu prices per mCore
    # obs: realistic prices e.g. based on commercial expensive CPUs
    p_cpu_list = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4]
    # it generates all the combination M*N where M,N are the lengths of the two lists
    # these combinations are
    gen = ((x, y) for x in p_cpu_list for y in T_horizon_avail)
    # configurations is a list of tuples
    for u, v in gen:
        configurations.append((u, v))
    # we return the maximum number allowed of configs
    # Warning: SISTEMA QUESTA COSA CONSIDERANDO CHE POI GLI USERS POSSONO INSERIRLA!!!!
    return configurations[:min(max_config_number, len(configurations))]
