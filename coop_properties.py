import numpy as np


def _is_individually_rational(payoff_vector):
    tmp = [payoff_vector[i] >= 0 for i in range(0, len(payoff_vector))]
    return False not in tmp


def _is_efficient(coal_payoff, payoff_vector):
    # we consider the presence of some approximation loss
    return abs(np.sum(payoff_vector) - coal_payoff) <= 0.1


def is_an_imputation(coal_payoff, payoff_vector):
    return _is_efficient(coal_payoff, payoff_vector) and _is_individually_rational(payoff_vector)


def is_group_rational(all_coal_payoffs, coal_payoff):
    return abs(max(all_coal_payoffs) - coal_payoff) >= 0.1


# The criterion is to compare the payoffs vectors
def best_coalition(info_all_coalitions):
    best_coalition = {}
    for i in range(len(info_all_coalitions)):
        for j in range(1, len(info_all_coalitions)):
            if (0, 'NO') in info_all_coalitions[i]["coalition"] or (0, 'NO') in info_all_coalitions[j]["coalition"]:
                tmp0 = False not in np.greater_equal(info_all_coalitions[i]["core"],
                                                     info_all_coalitions[j]
                                                     ["core"])
                tmp1 = False not in np.less_equal(info_all_coalitions[i]["core"], info_all_coalitions[j]
                ["core"])
                if tmp0:
                    best_coalition = info_all_coalitions[i]
                elif tmp1:
                    best_coalition = info_all_coalitions[j]
                else:
                    best_coalition = {}
    return best_coalition


def is_convex(coalitions_infos):
    convexity = []
    union_value = 0
    intersection_value = 0
    for i in range(len(coalitions_infos)):
        for j in (range(i + 1, len(coalitions_infos))):
            coal1 = coalitions_infos[i]["coalition"]
            coal2 = coalitions_infos[j]["coalition"]
            coal1_value = coalitions_infos[i]["coalitional_payoff"]
            coal2_value = coalitions_infos[j]["coalitional_payoff"]

            # searching for the union and intersection coalition
            tmp = tuple(set(coal1).union(coal2))
            union = sorted(tmp, key=lambda x: x[0])
            tmp = tuple(set(coal1).intersection(coal2))
            intersection = sorted(tmp, key=lambda x: x[0])
            if (0, 'NO') not in union:
                convexity.append(True)
            else:
                for k in coalitions_infos:

                    if k["coalition"] == intersection:
                        intersection_value = k["coalitional_payoff"]

                    if k["coalition"] == union:
                        union_value = k["coalitional_payoff"]

                # round values for the comparison
                if abs(union_value + intersection_value - coal1_value - coal2_value) >= 0:
                    convexity.append(True)
                else:
                    # print(union, union_value,coal1, coal2 )
                    # print(intersection, intersection_value)
                    # print(union_value - (coal1_value + coal2_value - intersection_value))
                    convexity.append(False)

    return False not in convexity
