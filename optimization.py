import math

from scipy.optimize import minimize
import numpy as np


class Foo:
    def get_params(self):
        return self.params

    def set_params(self, params):
        self.params = params

    def get_utilities(self):
        return self.utilities

    def set_utilities(self, utilities):
        self.utilities = utilities


foo = Foo()


def _genera_loads(daily_timeslots, avg_load):
    if avg_load == 0:
        return [0] * daily_timeslots
    np.random.seed(12)
    tmp = np.random.randint(avg_load - avg_load / 4, avg_load + avg_load / 4, daily_timeslots)
    return tmp


def _utility_i(beta_i, h_i, load_t, csi=0.8):
    return beta_i * load_t * (1 - math.exp(-csi * h_i))


def _revenues(daily_timeslots, SPs, betas, h_vec, etas):
    etas = [0] + etas
    # utility produced by each player for all the timeslots
    utilities = []

    for i in SPs:
        utility = 0
        loads_i = _genera_loads(daily_timeslots, etas[i])
        for t in range(daily_timeslots):
            utility += _utility_i(betas[i], h_vec[i], loads_i[t])

        utilities.append(utility)

    total_revenues = sum(utilities)
    utilities = [0] + utilities
    foo.set_utilities(utilities)
    return total_revenues


def _objective(x):
    p_cpu, daily_timeslots, coalition, players_numb, HC, betas, loads, expiration = foo.get_params()

    betas = [0] + betas
    h_vec = x[:-1]
    capacity = x[-1]
    if (0, "NO") in coalition:
        SPs_in_coalition = [l[0] for l in coalition[1:]]
        tmp = -expiration * _revenues(daily_timeslots, SPs_in_coalition, betas, h_vec, loads) + p_cpu * capacity
    else:
        tmp = 0
    return tmp


def _constraint1(x):
    return sum(x[:-1]) - x[-1]


def maximize_payoff(p_cpu, daily_timeslots, coalition, players_numb, HC, betas, avg_loads_all_players, expiration):
    params = p_cpu, daily_timeslots, coalition, players_numb, HC, betas, avg_loads_all_players, expiration
    foo.set_params(params)
    x0 = [1] * (players_numb + 1)
    b = (0, None)
    capacity_bnd = ((0, HC),)
    bnds = (b,) * players_numb + capacity_bnd
    con1 = {'type': 'eq', 'fun': _constraint1}
    cons = [con1]
    sol = minimize(_objective, x0, method='slsqp', bounds=bnds, constraints=cons)
    if not sol['success']:
        print(sol)
    return sol, foo.get_utilities()
