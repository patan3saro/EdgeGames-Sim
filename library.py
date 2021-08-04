import math
from itertools import chain, combinations

import numpy as np


def _all_permutations(iterable):
    "all_permutation([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return list(chain.from_iterable(combinations(s, r) for r in range(len(s) + 1)))


def feasible_permutations(N):
    set_players = [(i + 1) for i in range(N)]
    perms = _all_permutations(set_players)
    feasible_perms = []
    # to exclude the coalition with only NO we start from index 2
    for perm in perms[2:]:
        if 1 in perm:
            feasible_perms.append(perm)
    return feasible_perms


def generate_configs(N):
    '''
    tmp=np.random.randint(0,11,N)
    rand_array =
    fraction_resources_vector = [for i in range(N)]
    fraction_payments_vector=[]
    capacity =
    configuration= capacity)'''


def _f(resources, a):
    return (0.01 * a ** 2 + resources - 0.01 * (resources - a) ** 2) ** 0.999


def _g(load, player):
    return (20 / (1 + pow(math.e, -(pow(load, 0.5) - 6)))) - 2

#this function generates load randomly
def _generate_load(eta,sigma):
    np.random.randint(eta-sigma/2, eta+sigma/2)
    return

def player_utility(resources, player):
    # if a real time SP, e.g. Peugeot
    if player == "rt":
        # gets a great benefit from resources at the edge with this a
        a = 10
        load = _generate_load()
    # if not real time SP, e.g. Netflix
    else:
        # gets less benefit
        a = 0
        load = _generate_load()
    return _f(resources, a) * _g(load)




def coal_payoff():
    v = time_sum_all_utilities - p_cpu * capacity
    return


# OPTIMIZATION

def objective(x):
    capacity = x[0]

    return
