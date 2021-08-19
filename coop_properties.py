import math


def is_individually_rational(self, payoff_vector):
    tmp = [payoff_vector[i] >= 0 for i in range(0, len(payoff_vector))]
    return False not in tmp


def is_efficient(self, coal_payoff, payoff_vector):
    # we consider the presence of some approximation loss
    return abs(sum(payoff_vector) - coal_payoff) <= 0.5


def is_an_imputation(self):
    return self.is_efficient() and self.is_individually_rational()


def is_convex(self, coalitions_infos, game_type):
    convexity = []
    tmp = ""
    union_value = 0
    intersection_value = 0
    if game_type == "first":
        tmp = "coalitional_payoff"
    elif game_type == "second":
        tmp = "second_game_coalitional_payoff"

    for i in range(len(coalitions_infos)):
        for j in (range(i + 1, len(coalitions_infos))):
            coal1 = coalitions_infos[i]["coalition"]
            coal2 = coalitions_infos[j]["coalition"]
            coal1_value = coalitions_infos[i][tmp]
            coal2_value = coalitions_infos[j][tmp]

            # searching for the union and intersection coalition
            union = tuple(set(coal1).union(coal2))
            intersection = tuple(set(coal1).intersection(coal2))

            if (0, 'NO') not in union:
                convexity.append(True)
            else:
                for k in coalitions_infos:
                    if k["coalition"] == intersection:
                        intersection_value = k[tmp]

                    if k["coalition"] == union:
                        union_value = k[tmp]
                        print(k["coalition"], union)
                        print(k[tmp])
                # round values for the comparison
                if math.ceil(union_value) >= coal1_value + coal2_value - intersection_value:
                    convexity.append(True)
                else:
                    # print(union, union_value,coal1, coal2 )
                    # print(intersection, intersection_value)
                    # print(union_value - (coal1_value + coal2_value - intersection_value))
                    convexity.append(False)

    return False not in convexity
