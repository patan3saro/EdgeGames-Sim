import math
import numpy as np
from scipy.optimize._minimize import minimize

import core
import utils


class Game:

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
        tmp = np.random.randint(eta - sigma / 2, eta + sigma / 2)
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
            eta = 500
            sigma = 50
            load = self._generate_load(eta, sigma)
        # if not real time SP, e.g. Netflix
        else:
            # gets less benefit
            a = 0.005
            # we must generate a load that is comparable
            # with the curve of the load benefit _g
            # e.g. choose eta=height_of_g/1.1
            # eta and sigma must be positive and eta >= sigma/2
            eta = 140
            sigma = 20
            load = self._generate_load(eta, sigma)
        return self._f(resources, a) * self._g(load)

    def _2_player_utility_t(self, player_type):
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
            eta = 150
            sigma = 50
            load = self._generate_load(eta, sigma)
        # benefit factor dollars per mCore per minute
        # see: https://edge.network/en/pricing/
        beta = self.get_params()[5]
        # converting load in needed resources
        converted_load = load * conversion_factor
        return converted_load

    # max payoff computation
    def calculate_coal_payoff(self):

        p_cpu, T_horizon, coalition, _, simulation_type, beta, players_numb = self.get_params()
        # matrix with all the b for each player
        # rows = players  // columns = time steps in time horizon
        B_eq = []
        N = players_numb
        if simulation_type == "real":
            utility_f = self._2_player_utility_t
        else:
            utility_f = self._1_player_utility_t

        # if the network operator is not in the coalition or It is alone etc...
        if (0, 'NO') not in coalition or ((0, 'NO'),) == coalition or (len(coalition) == 0) or (len(coalition) == 1):
            b_eq = [0] * T_horizon
        else:
            b_eq = []
            # we calculate utility function at t for a player only for SPs
            # coalition is a tuple that specify the type of player also
            for t in range(T_horizon):
                tot_utility = 0
                tmp_arr = [0] * players_numb
                for player in coalition[1:]:
                    player_type = player[1]
                    tmp0 = utility_f(player_type)
                    tot_utility += tmp0
                    tmp_arr[player[0]] = tmp0
                B_eq.append(tmp_arr)
                b_eq.append(tot_utility)
            B_eq = np.matrix(B_eq)

        # cost vector with benefit factor and cpu price
        # we use a minimize-function, so to maximize we minimize the opposite
        c = np.array([beta] * T_horizon + [-p_cpu])

        A_eq = np.append(np.identity(T_horizon), np.zeros(shape=(T_horizon, 1)), axis=1)
        A_ub = np.append(-np.identity(T_horizon), np.ones(shape=(T_horizon, 1)), axis=1)
        b_eq = np.array(b_eq)
        b_ub = np.zeros(shape=T_horizon)
        B = np.transpose(np.concatenate((B_eq, np.zeros(shape=(5, 3)))))
        # for A_ub and b_ub I change the sign to reduce the matrices in the desired form
        bounds = ((0, None),) * (T_horizon + 1)
        params = (c, A_ub, A_eq, b_ub, b_eq, bounds, B)
        sol = core.find_core(params)
        return sol

    def calculate_coal_payoff_second_game(self):
        # I get in this way the parameters because the signature of
        # the objective func must be like this
        _, T_horizon, coalition, _, simulation_type, _, _ = self.get_params()
        if (0, 'NO') not in coalition or ((0, 'NO'),) == coalition:
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
            utility_time_sum = T_horizon * utility_f(player_type)
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

    def shapley_value_payoffs(self, best_coalition, infos_all_coal_one_config, players_number, coalitions, game_type):
        coalition_players_number = len(best_coalition)
        x_payoffs = []
        N_factorial = math.factorial(players_number)
        tmp0 = ""
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
