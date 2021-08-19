from scipy.optimize import linprog


def find_core(params):
    # number of slots
    c, A_ub, A_eq, b_ub, b_eq, bounds = params

    pippo = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=None, method='interior-point',
                    callback=None, options=None, x0=None)
    print(pippo)
    return pippo
