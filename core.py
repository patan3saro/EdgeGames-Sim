from scipy.optimize import linprog


def find_core(params):
    # number of slots
    c, A_ub, b_ub, A_eq, b_eq, bounds, T_horizon = params
    # print("c", c, "A_ub", A_ub, "b_ub", b_ub)
    primal_sol = linprog(-c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, method='revised simplex')
    return primal_sol
