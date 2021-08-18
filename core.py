import pulp as plp
import math
import numpy as np
from itertools import combinations


def find_core(vf):
    N = len(vf) + 1
    N = int(math.log(N, 2))
    PL = list(range(N))

    model = plp.LpProblem(name="core")
    x_var = {n:
        plp.LpVariable(
            cat=plp.LpContinuous,
            lowBound=None,
            upBound=None,
            name="x_{0}".format(str(n))
        ) for n in PL
    }

    cons = {}

    for i in range(1, N + 1):
        se = plp.LpConstraintGE if i < N else plp.LpConstraintEQ
        for com in combinations(PL, i):
            vf_ = vf[com]
            c_ = plp.LpConstraint(
                e=plp.lpSum(x_var[n] for n in com),
                sense=se,
                rhs=vf_,
                name="cons_{0}".format(com))
            cons[com] = c_
    for c in cons: model.addConstraint(cons[c])

    objective = plp.lpSum(x_var[n] * 0 for n in PL)
    model.sense = plp.LpMaximize
    model.setObjective(objective)

    status = model.solve()
    core = np.array([x_var[n].varValue for n in PL])
    return core
