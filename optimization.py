import math

from scipy.optimize import minimize
import numpy as np


class Comodo:
    def get_params(self):
        return self.params

    def set_params(self, params):
        self.params = params


comodo = Comodo()

def _genera_loads(T_horizon, avg_load):
    if avg_load == 0:
        return [0] * T_horizon
    np.random.seed(12)
    tmp = np.random.randint(avg_load - avg_load / 4, avg_load + avg_load / 4, T_horizon)
    return tmp


def _utility_i(beta_i, h_i, load_t, csi=0.8, s=0.5):
    # return beta_i * pow(h_i, csi / s) * pow(load_t, csi)
    return beta_i * load_t * (1 - math.exp(-csi * h_i))


def _revenues(T_horizon, SPs, betas, h_vec, etas):
    summation = 0
    etas = [0] + etas
    for i in SPs:
        loads_i = _genera_loads(T_horizon, etas[i])
        for t in range(T_horizon):
            summation += _utility_i(betas[i], h_vec[i], loads_i[t])
    return summation


def _objective(x):
    p_cpu, T_horizon, coalition, players_numb, HC, betas, loads, expiration = comodo.get_params()

    betas = [0] + betas
    h_vec = x[:-1]
    capacity = x[-1]
    if (0, "NO") in coalition:
        SPs_in_coalition = [l[0] for l in coalition[1:]]
        tmp = -expiration * _revenues(T_horizon, SPs_in_coalition, betas, h_vec, loads) + p_cpu * capacity
    else:
        tmp = 0
    return tmp


def _constraint1(x):
    return sum(x[:-1]) - x[-1]


def maximize_payoff(p_cpu, T_horizon, coalition, players_numb, HC, betas, avg_loads_all_players, expiration):
    params = p_cpu, T_horizon, coalition, players_numb, HC, betas, avg_loads_all_players, expiration
    comodo.set_params(params)
    x0 = [1] * (players_numb + 1)
    b = (0, None)
    capacity_bnd = ((0, HC),)
    bnds = (b,) * players_numb + capacity_bnd
    con1 = {'type': 'eq', 'fun': _constraint1}
    cons = [con1]
    sol = minimize(_objective, x0, method='slsqp', bounds=bnds, constraints=cons)
    if not sol['success']:
        print(sol)
    return sol
