import math
import numpy as np

import coop_properties as cp
import core
from scipy.optimize import linprog


class Game:

    # this function generates load randomly
    def _generate_load(self, eta, sigma):
        np.random.seed(10)
        # WARNING: randomness generates problems with the optimization
        tmp = np.random.randint(eta - sigma / 2, eta + sigma / 2)
        return tmp

    def _player_utility_t(self, player_type):
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
        # converting load in needed resources
        converted_load = load * conversion_factor
        return converted_load

    def calculate_coal_payoff(self):
        p_cpu, T_horizon, coalition, _, beta, players_numb, chi, alpha, HC = self.get_params()
        # matrix with all the b for each player
        b = [0] * (players_numb * T_horizon)
        # if the network operator is not in the coalition or It is alone etc...
        if (0, 'NO') not in coalition or ((0, 'NO'),) == coalition or (len(coalition) == 0) or (len(coalition) == 1):
            pass
        else:
            # we calculate utility function at t for a player only for SPs
            # coalition is a tuple that specify the type of player also
            indx = 2
            for player in coalition[1:]:
                # in the paper y_t^S
                for t in range(T_horizon):
                    player_type = player[1]
                    tmp0 = self._player_utility_t(player_type)
                    print(tmp0)
                    b[indx] = tmp0
                    indx += 1
                # we divide by 2 the used resources because we need to split the payoff in a non fair way adding a
                # false use of resources by the NO in order to pay the NO for his presence, in fact the cpu exists
                # thanks to him

        # cost vector with benefit factor and cpu price
        # we use a minimize-function, so to maximize we minimize the opposite
        # Creating c vector
        tmp0 = beta * np.ones(shape=(players_numb * T_horizon))
        tmp1 = -chi * np.ones(shape=(players_numb * T_horizon))
        tmp2 = np.zeros(shape=(players_numb))
        c = np.concatenate((tmp0, tmp1, tmp2, [-p_cpu]), axis=0)
        # Creating A matrix
        identity = np.identity(players_numb * T_horizon)
        zeros = np.zeros(shape=(players_numb * T_horizon, players_numb * T_horizon))
        zeros_column = np.zeros(shape=(players_numb * T_horizon, 1))
        tmp0 = np.zeros(shape=(players_numb * T_horizon, players_numb))
        mega_row_A0 = np.concatenate((identity, zeros, tmp0, zeros_column), axis=1)

        tmp = 0
        for col in range(players_numb):
            for row in range(T_horizon):
                tmp0[row + tmp, col] = -1
            tmp += T_horizon

        mega_row_A1 = np.concatenate((identity, zeros, tmp0, zeros_column), axis=1)

        mega_row_A2 = np.concatenate((zeros, identity, -tmp0, zeros_column), axis=1)

        tmp = np.zeros(shape=(players_numb * T_horizon, players_numb))
        mega_row_A3 = np.concatenate((zeros, identity, tmp, zeros_column), axis=1)

        tmp0 = np.zeros(shape=(2, 2 * players_numb * T_horizon))
        tmp1 = np.ones(shape=(1, players_numb))
        tmp2 = np.zeros(shape=(1, players_numb))
        tmp1 = np.concatenate((tmp1, tmp2), axis=0)
        tmp2 = np.transpose(np.matrix([[-1, 1]]))
        mega_row_A4 = np.concatenate((tmp0, tmp1, tmp2), axis=1)

        A = np.concatenate((mega_row_A0, mega_row_A1, mega_row_A2, mega_row_A3, mega_row_A4), axis=0)
        tmp0 = np.zeros(shape=(players_numb * T_horizon))
        b = np.concatenate((b, tmp0, b, tmp0, [0, HC]), axis=0)
        # for A_ub and b_ub I change the sign to reduce the matrices in the desired form
        bounds = ((0, None),) * (2 * players_numb * T_horizon + players_numb + 1)
        params = (c, A, b, bounds, T_horizon)
        sol = core.find_core(params)

        return sol

    def calculate_core(self, infos_all_coal_one_config):
        A_eq = [[1, 1, 1]]
        b_eq = -infos_all_coal_one_config[-1]["coalitional_payoff"]
        A = [[-1, 0, 0], [0, -1, 0], [0, 0, -1], [-1, -1, 0], [-1, 0, -1], [0, -1, -1]]
        b = []
        for info in infos_all_coal_one_config[:-1]:
            b.append(info["coalitional_payoff"])
        coefficients_min_y = [0] * (len(A[0]))
        res = linprog(coefficients_min_y, A_eq=A_eq, b_eq=b_eq, A_ub=A, b_ub=b)

        return res['x']

    def is_convex(self, coalitions_infos):
        return cp.is_convex(coalitions_infos)

    def verify_properties(self, all_coal_payoff, coal_payoff, payoffs_vector):
        print("Verifying properties of payoffs \n")
        if cp.is_an_imputation(-coal_payoff, payoffs_vector):
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
                        contribution = q["coalitional_payoff"] - S["coalitional_payoff"]
                        tmp = math.factorial(len(S["coalition"])) * math.factorial(
                            players_number - len(S["coalition"]) - 1) * contribution
                        summation = summation + tmp
            x_payoffs.append((1 / N_factorial) * summation)

        return x_payoffs

    def how_much_rev_paym(self, payoff_vector, w, Capacity):
        p_cpu, _, _, _, beta, players_numb, _, _, _ = self.get_params()
        beta_vec = [0, 0, beta]
        A_eq = [[1, 0, 0, -1, 0, 0], [0, 1, 0, 0, -1, 0], [0, 0, 1, 0, 0, -1], [1, 1, 1, 0, 0, 0]]
        b_eq = [payoff_vector[0], payoff_vector[1], payoff_vector[2], np.matmul(w, beta_vec)]

        coefficients_min_y = [0] * (len(A_eq[0]))
        res = linprog(coefficients_min_y, A_eq=A_eq, b_eq=b_eq)
        return res['x'][0:3], res['x'][3:]

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
