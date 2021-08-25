import math
import numpy as np

import coop_properties as cp
import core


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
            conversion_factor = 20
            # we must generate a load that is comparable
            # with the curve of the load benefit _g
            # e.g. choose eta=height_of_g/1.2
            # eta and sigma must be positive and eta >= sigma/2
            eta = 2000
            sigma = 80
            load = self._generate_load(eta, sigma)
        # if not real time SP, e.g. Netflix
        else:
            # used to convert load in mCore
            conversion_factor = 5
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
        N = players_numb
        B_eq = np.zeros(shape=(T_horizon, N))

        if simulation_type == "real":
            utility_f = self._2_player_utility_t
        else:
            utility_f = self._1_player_utility_t

        # if the network operator is not in the coalition or It is alone etc...
        if (0, 'NO') not in coalition or ((0, 'NO'),) == coalition or (len(coalition) == 0) or (len(coalition) == 1):
            b_eq = [0] * T_horizon
            B_eq = np.zeros(shape=(2 * T_horizon, N))
        else:
            b_eq = []
            # we calculate utility function at t for a player only for SPs
            # coalition is a tuple that specify the type of player also
            for t in range(T_horizon):
                # in the paper y_t^S
                used_resources = 0
                tmp_arr = [0] * players_numb
                for player in coalition[1:]:
                    player_type = player[1]
                    tmp0 = utility_f(player_type)
                    used_resources += tmp0
                    tmp_arr[player[0]] = tmp0
                # we divide by 2 the used resources because we need to split the payoff in a non fair way adding a
                # false use of resources by the NO in order to pay the NO for his presence, in fact the cpu exists
                # thanks to him
                B_eq = np.insert(B_eq, t, tmp_arr, axis=0)
                b_eq.append(used_resources)

        # cost vector with benefit factor and cpu price
        # we use a minimize-function, so to maximize we minimize the opposite
        c = np.array([beta] * T_horizon + [-p_cpu])

        A_eq = np.append(np.identity(T_horizon), np.zeros(shape=(T_horizon, 1)), axis=1)
        A_ub = np.append(-np.identity(T_horizon), np.ones(shape=(T_horizon, 1)), axis=1)
        b_eq = np.array(b_eq)
        b_ub = np.zeros(shape=T_horizon)

        B = np.transpose(B_eq)
        # for A_ub and b_ub I change the sign to reduce the matrices in the desired form
        bounds = ((0, None),) * (T_horizon + 1)
        params = (c, A_ub, A_eq, b_ub, b_eq, bounds, B, T_horizon)
        sol = core.find_core(params)

        return sol

    def verify_properties(self, all_coal_payoff, coal_payoff, payoffs_vector, game_type):
        print("Verifying properties of core (", game_type, "game )\n")
        if cp.is_an_imputation(coal_payoff, payoffs_vector):
            print("Core is an imputation (efficiency + individual rationality)!\n")
            print("Check if payoff vector is group rational...\n")
            if cp.is_group_rational(all_coal_payoff, coal_payoff):
                print("The payoff vector is group rational!\n")
                print("The payoff vector is in the core!\n")
                print("Core verification terminated SUCCESSFULLY!\n")
                return True
            else:
                print("The payoff vector isn't group rational!\n")
                print("The payoff vector is not in the core!\n")
                print("Core verification terminated unsuccessfully!\n")
        else:
            print("The payoff vector isn't an imputation\n")
            print("Core verification terminated unsuccessfully!\n")
        return False

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
