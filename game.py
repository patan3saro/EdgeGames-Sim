import math
from scipy.optimize import minimize
from optimization import maximize_payoff


class Game:

    def calculate_coal_payoff(self):
        p_cpu, T_horizon, coalition, _, beta, players_numb, chi, alpha, HC, betas, gammas, loads, expiration = self.get_params()
        sol = maximize_payoff(p_cpu, T_horizon, coalition, players_numb, HC, betas, loads, expiration)
        return sol

    def shapley_value_payoffs(self, infos_all_coal_one_config, players_number, coalitions):
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

    def how_much_rev_paym(self, payoff_vector, w):

        p_cpu, T_horizon, coalition, _, beta, players_numb, chi, alpha, HC, betas, gammas, loads, expiration = self.get_params()

        def _constraint_split_1(x):
            return sum(x[3:]) - p_cpu * w[-1]

        def _constraint_split_2(x):
            return x[0] - x[3] - payoff_vector[0]

        def _constraint_split_3(x):
            return x[1] - x[4] - payoff_vector[1]

        def _constraint_split_4(x):
            return x[2] - x[5] - payoff_vector[2]

        x0 = [1] * 2 * players_numb
        b = (None, None)
        bnds = (b,) * players_numb * 2
        con1 = {'type': 'eq', 'fun': _constraint_split_1}
        con2 = {'type': 'eq', 'fun': _constraint_split_2}
        con3 = {'type': 'eq', 'fun': _constraint_split_3}
        con4 = {'type': 'eq', 'fun': _constraint_split_4}
        cons = [con1, con2, con3, con4]
        def obj(x):
            return 5
        res = minimize(obj, x0, method='slsqp', bounds=bnds, constraints=cons)
        return res['x'][0:players_numb], res['x'][players_numb:]

    # GETTERS AND SETTERS
    # to get parameters p_cpu, T_horizon, coalition, players_number
    def get_params(self):
        return self.params

    def set_params(self, params):
        self.params = params
