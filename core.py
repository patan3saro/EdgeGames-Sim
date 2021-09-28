from scipy.optimize import linprog


def find_core(params):
    # number of slots
    c, A_ub, b_ub, bounds, T_horizon = params
    #print("c", c, "A_ub", A_ub, "b_ub", b_ub)
    primal_sol = linprog(-c, A_ub=A_ub, b_ub=b_ub, method='interior-point')
    return primal_sol
