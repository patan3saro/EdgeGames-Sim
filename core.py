import numpy as np
from scipy.optimize import linprog


def find_core(params):
    # number of slots
    c, A_ub, b_ub, bounds, B, T_horizon = params

    #print("c", c, "A_ub", A_ub, "b_ub", b_ub, "B", B)
    primal_sol = linprog(-c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='interior-point')
    capacity = primal_sol['x'][-1]

    c_d = b_ub
    A_td = -np.transpose(A_ub)
    b_ubd = -c
    bounds = ((0, None),) * (5 * T_horizon)  # attention!!!!!
    # print("c", c_d, "A_ub", A_td, "b_ub", b_ubd, "B", B, )
    dual_sol = linprog(c_d, A_ub=A_td, b_ub=b_ubd, bounds=bounds, method='interior-point')

    # checking if the coal payoff of the primal and dual is the same
    if not (abs(-primal_sol['fun'] - dual_sol['fun']) < 0.1):
        print("ERROR: the payoff of primal and dual is not the same!\n")

    payoff_vector = np.matmul(B, dual_sol['x'])
    # WARNING the solution exceeds the tolerance because of the randomness during the load generation:
    # to proof this try with a static load

    # second game values

    coal_payoff_second = c[0] * np.sum(primal_sol['x'][:-1])

    print(primal_sol['x'])
    proportions_array = payoff_vector / (np.sum(payoff_vector) + 0.0000001)
    second_game_payoff_vector = np.multiply(proportions_array, coal_payoff_second)

    return dual_sol, payoff_vector, capacity, coal_payoff_second, second_game_payoff_vector
