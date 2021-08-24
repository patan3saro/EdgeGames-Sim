import numpy as np
from scipy.optimize import linprog


def find_core(params):
    # number of slots
    c, A_ub, A_eq, b_ub, b_eq, bounds, B = params
    primal_sol = linprog(-c, A_ub=-A_ub, b_ub=-b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='interior-point')
    capacity = primal_sol['x'][-1]

    c_d = np.concatenate((b_eq, b_ub))
    A_td = np.transpose(np.concatenate((A_eq, A_ub)))
    b_ubd = c
    bounds0 = ((None, None),) * 5
    bounds1 = ((None, 0),) * 5
    bounds = bounds0 + bounds1

    dual_sol = linprog(c_d, A_ub=-A_td, b_ub=-b_ubd, bounds=bounds, method='interior-point')

    payoff_vector = np.matmul(B, dual_sol['x'])
    # WARNING the solution exceeds the tolerance because of the randomness during the load generation:
    # to proof this try with a static load

    # second game values

    coal_payoff_second = c[0] * np.sum(primal_sol['x'])
    print(coal_payoff_second - dual_sol['fun'], primal_sol['x'])
    proportions_array = payoff_vector / (np.sum(payoff_vector) + 0.0000001)
    second_game_payoff_vector = np.multiply(proportions_array, coal_payoff_second)

    return dual_sol, payoff_vector, capacity, coal_payoff_second, second_game_payoff_vector
