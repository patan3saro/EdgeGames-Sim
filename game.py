import math
import numpy as np
from itertools import chain, combinations
from scipy.optimize._minimize import minimize


class Game:

    def _all_permutations(self, iterable):
        "all_permutation([0,1,2]) --> () (0,) (1,) (2,) (0,1) (0,2) (1,2) (0,1,2)"
        s = list(iterable)
        return list(chain.from_iterable(combinations(s, r) for r in range(len(s) + 1)))

    def feasible_permutations(self, players_number, rt_players):
        set_players = []

        if rt_players is None:
            # one half rt and the other half nrt
            rt_players = round((players_number - 1) / 2)
        # assign type to players
        for i in range(players_number):
            # valid only for SPs
            # SPs NRT
            if i != 0 and rt_players > 0:
                set_players.append((i, "rt"))
                rt_players -= 1
            # SPs NRT
            elif i != 0:
                set_players.append((i, "nrt"))
            # NO
            else:
                set_players.append((i, "NO"))

        perms = self._all_permutations(set_players)
        feasible_perms = []
        # to exclude the coalition with just the NO and empty coalition we start from index 2
        for perm in perms[2:]:
            if 0 in perm[0]:
                feasible_perms.append(perm)
        return perms

    # we can provide the number of config to try
    # inputs: type of slots, it can be seconds or minutes
    # realistic time horizon of a cpu
    def generate_configs(self, max_config_number=23, type_slot='min', years_horizon=3):
        # available time horizons
        configurations = []
        one_year_minutes = 525600
        one_year_seconds = 3.154e+7
        T_horizon_avail = []
        if type_slot == "sec":
            t = one_year_seconds
        elif type_slot == "min":
            t = one_year_minutes
        for i in range(years_horizon):
            T_horizon_avail.append(t * (i + 1))
        # available cpu prices per mCore
        # obs: realistic prices e.g. based on commercial expensive CPUs
        p_cpu_list = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4]
        # it generates all the combination M*N where M,N are the lengths of the two lists
        # these combinations are
        gen = ((x, y) for x in p_cpu_list for y in T_horizon_avail)
        # configurations is a list of tuples
        for u, v in gen:
            configurations.append((u, v))
        # we return the maximum number allowed of configs
        # Warning: SISTEMA QUESTA COSA CONSIDERANDO CHE POI GLI USERS POSSONO INSERIRLA!!!!
        return configurations[:min(max_config_number, len(configurations))]

    # useful functions to create the utility at time t for each player
    def _f(self, resources, a):
        # we must saturate the number of resources to obtain  solution>=0
        # in fact one of the intersection with axis x (y=0) is in x=0 --> y=0
        # the other one is in x=2a+100 (found solving the equation)
        # h determines the spread of the curve
        # and we need a great spread because the number of resources
        # can be in the order of 10^3 or 10^4
        q = 0.0001
        resources = min(resources, (2 * a + (1 / q)))
        # resources is by default > 0 thanks to the bounds in minimize function
        # so we will have always _f>=0
        return q * (a ** 2) + resources - q * (resources - a) ** 2

    def _g(self, load):
        # h (height) determine the saturation value
        c = 50
        # this lowers the function
        l = 0.5
        # determines the slope og the function
        s = 0.03
        # m moves to the right  if >0 else to the left the function
        m = 5
        return (c / (1 + math.e ** (- (load * s - m)))) - l

    # this function generates load randomly
    def _generate_load(self, eta, sigma):
        # WARNING: randomness generates problems with the optimization
        tmp = eta  # np.random.randint(eta - sigma/2, eta + sigma/2)
        return tmp

    def _1_player_utility_t(self, resources, player_type):
        # if a real time SP, e.g. Peugeot
        if player_type == "rt":
            # gets a great benefit from resources at the edge with this a
            a = 0.2
            # we must generate a load that is comparable
            # with the curve of the load benefit _g
            # e.g. choose eta=height_of_g/1.2
            # eta and sigma must be positive and eta >= sigma/2
            eta = 20
            sigma = 4
            load = self._generate_load(eta, sigma)
        # if not real time SP, e.g. Netflix
        else:
            # gets less benefit
            a = 0.005
            # we must generate a load that is comparable
            # with the curve of the load benefit _g
            # e.g. choose eta=height_of_g/1.1
            # eta and sigma must be positive and eta >= sigma/2
            eta = 14
            sigma = 2
            load = self._generate_load(eta, sigma)
        return self._f(resources, a) * self._g(load)

    def _2_player_utility_t(self, resources, player_type):
        # if a real time SP, e.g. Peugeot
        if player_type == "rt":
            # used to convert load in mCore
            conversion_factor = 200
            # we must generate a load that is comparable
            # with the curve of the load benefit _g
            # e.g. choose eta=height_of_g/1.2
            # eta and sigma must be positive and eta >= sigma/2
            eta = 20000
            sigma = 80
            load = self._generate_load(eta, sigma)
        # if not real time SP, e.g. Netflix
        else:
            # used to convert load in mCore
            conversion_factor = 50
            # we must generate a load that is comparable
            # with the curve of the load benefit _g
            # e.g. choose eta=height_of_g/1.1
            # eta and sigma must be positive and eta >= sigma/2
            eta = 10000
            sigma = 50
            load = self._generate_load(eta, sigma)
        # benefit factor dollars per mCore per minute
        # see: https://edge.network/en/pricing/
        beta = 0.007 / (60 * 4000)
        # converting load in needed resources
        converted_load = load * conversion_factor
        # the utility saturate if converted load>resources
        variable = min(converted_load, resources)
        return beta * variable

    # to calculate the coalitional utility we simulate intervals

    def coal_payoff_objective_function(self, x):
        # I get in this way the parameters because the signature of
        # the objective func must be like this
        p_cpu, T_horizon, coalition, _, simulation_type = self.get_params()
        capacity = x[0]
        resources = x[1:]
        tot_utility = 0
        # if the network operator is not in the coalition or It is alone
        if (0, 'NO') not in coalition or ((0, 'NO'),) == coalition:
            return 0
        if simulation_type == "real":
            utility_f = self._2_player_utility_t
        else:
            utility_f = self._1_player_utility_t

        # we calculate utility function at t for a player only for SPs
        # coalition is a tuple that specify the type of player also
        i = 1
        for player in coalition[1:]:
            utility_time_sum = 0
            player_type = player[1]
            # WARNING: correct this multiplication with and explain why you deleted loop!
            # for t in range(T_horizon):
            # remember that resources is a vector
            # utility_time_sum = utility_time_sum + utility_f(resources[player[0]-1], player_type)
            utility_time_sum = T_horizon * utility_f(resources[i - 1], player_type)
            tot_utility = tot_utility + utility_time_sum
            i += 1
        # we use minimize function, so to maximize we minimize the opposite
        return -(tot_utility - p_cpu * capacity)

    # OPTIMIZATION
    def constraint1(self, x):
        players_number = self.get_params()[3]
        eq = x[0]
        for i in range(players_number - 1):
            eq -= x[i + 1]
        return eq

    # max payoff computation
    def calculate_coal_payoff(self):
        con1 = {'type': 'eq', 'fun': self.constraint1}
        cons = [con1]
        players_number = self.get_params()[3]
        x0 = [1000]
        for i in range(players_number - 1):
            x0.append(x0[0] / players_number)
        # I bound the capacity: first item in tuple
        bnds = ((0, None),) * players_number
        sol = minimize(self.coal_payoff_objective_function, x0, bounds=bnds, method='SLSQP', constraints=cons)
        return sol

    def calculate_coal_payoff_second_game(self, resources):
        # I get in this way the parameters because the signature of
        # the objective func must be like this
        _, T_horizon, coalition, _, simulation_type = self.get_params()
        if (0, 'NO') not in coalition or ((0, 'NO'),) == coalition:
            print(coalition)
            return 0
        tot_utility = 0
        # if the network operator is not in the coalition or It is alone
        if (0, 'NO') not in coalition or ((0, 'NO'),) == coalition:
            return 0
        if simulation_type == "real":
            utility_f = self._2_player_utility_t
        else:
            utility_f = self._1_player_utility_t

        # we calculate utility function at t for a player only for SPs
        # coalition is a tuple that specify the type of player also
        i = 1
        for player in coalition[1:]:
            utility_time_sum = 0
            player_type = player[1]
            # WARNING: correct this multiplication with and explain why you deleted loop!
            # for t in range(T_horizon):
            # remember that resources is a vector
            # utility_time_sum = utility_time_sum + utility_f(resources[player[0]-1], player_type)
            utility_time_sum = T_horizon * utility_f(resources[i - 1], player_type)
            tot_utility = tot_utility + utility_time_sum
            i += 1
        # we use minimize function, so to maximize we minimize the opposite
        return tot_utility

    def calculate_payoff_vector(self, coal_payoff, coalition, players_numb):
        payoff_vector = [0] * players_numb
        for player in coalition:
            if len(player) != 0:
                payoff_vector[player[0]] = coal_payoff / len(coalition)
        return payoff_vector

    # To check properties
    def best_coalition(self, info_all_coalitions):
        best_coalition = {}
        for i in range(len(info_all_coalitions)):
            for j in range(1, len(info_all_coalitions)):
                if (0, 'NO') in info_all_coalitions[i]["coalition"] or (0, 'NO') in info_all_coalitions[j]["coalition"]:
                    tmp0 = False not in np.greater_equal(info_all_coalitions[i]["payoffs_vector"],
                                                         info_all_coalitions[j]
                                                         ["payoffs_vector"])
                    tmp1 = False not in np.less_equal(info_all_coalitions[i]["payoffs_vector"], info_all_coalitions[j]
                    ["payoffs_vector"])
                    if tmp0:
                        best_coalition = info_all_coalitions[i]
                    elif tmp1:
                        best_coalition = info_all_coalitions[j]
                    else:
                        best_coalition = {}
        return best_coalition

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
                    # round values for the comparison
                    if math.ceil(union_value) >= coal1_value + coal2_value - intersection_value:
                        convexity.append(True)
                    else:
                        #print(union, union_value)
                        #print(intersection, intersection_value)
                        #print(union_value - (coal1_value + coal2_value - intersection_value))
                        convexity.append(False)

        return False not in convexity

    def shapley_value_payoffs(self, best_coalition, infos_all_coal_one_config, players_number, coalitions, game_type):
        coalition_players_number = len(best_coalition)
        x_payoffs = []
        N_factorial = math.factorial(players_number)

        if game_type == "first":
            tmp0 = "coalitional_payoff"
        elif game_type == "second":
            tmp0 = "second_game_coalitional_payoff"

        for player in coalitions[-1]:
            coalitions_dict_without_i = []
            coalitions_dict_with_i = []
            for coalition_dict in infos_all_coal_one_config:
                if player not in coalition_dict["coalition"]:
                    coalitions_dict_without_i.append(coalition_dict)
                else:
                    coalitions_dict_with_i.append(coalition_dict)
            summation = 0
            for S in coalitions_dict_without_i:
                for q in coalitions_dict_with_i:
                    if tuple(set(S["coalition"]).symmetric_difference(q["coalition"])) == (player,):
                        contribution = q[tmp0] - S[tmp0]
                        tmp = math.factorial(len(S["coalition"])) * math.factorial(
                            players_number - len(S["coalition"]) - 1) * contribution
                        summation = summation + tmp
            x_payoffs.append((1 / N_factorial) * summation)

        return x_payoffs

    def how_much_must_pay(self, a):
        difference = []
        zip_object = zip(a[1], a[0])
        for list1_i, list2_i in zip_object:
            difference.append(list1_i - list2_i)

        return difference

    # GETTERS AND SETTERS
    # to get parameters p_cpu, T_horizon, coalition, players_number
    def get_params(self):
        return self.params

    def set_params(self, params):
        self.params = params

    def get_coal_payoff_second_game(self):
        return self.coal_payoff_second_game

    def set_coal_payoff_second_game(self, payoff):
        self.coal_payoff_second_game = payoff
