import numpy as np
from scipy.optimize import linprog


def find_core(params):
    # number of slots
    c, A_ub, A_eq, b_ub, b_eq, bounds, B = params

    primal_sol = linprog(-c, A_ub=-A_ub, b_ub=-b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='interior-point',
                         callback=None, options=None, x0=None)

    c_d = -np.concatenate((b_eq, b_ub))
    A_td = np.transpose(np.concatenate((A_eq, A_ub)))
    b_ubd = c
    bounds0 = ((None, None),) * 5
    bounds1 = ((None, 0),) * 5
    bounds = bounds0 + bounds1
    dual_sol = linprog(c_d, A_ub=-A_td, b_ub=-b_ubd, A_eq=None, b_eq=None, bounds=bounds, method='interior-point',
                       callback=None, options=None, x0=None)
    print(primal_sol['fun'], dual_sol['fun'])
    payoff_vector = np.matmul(B, dual_sol['x'])
    print(np.sum(payoff_vector) == -primal_sol['fun'])
    return dual_sol
