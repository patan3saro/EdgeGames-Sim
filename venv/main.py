import numpy as np
import math

def main(horizon_T, slot_t, capacity, players_number):
    # feasible permutation are 2^(N-1)-1 instead of 2
    coalitions=feasible_permutations(players_number)
    # ATTENTION: the configuration does nothing because it is not mandatory if we use scipy to optimize our function
    configurations = generate_configs()

    for configuration in configurations:
        # list of all the payoff for different coalitions
        coal_payoffs = []
        argmaxs_list = []

        for coalition in coalitions:
            #total payoff is the result of the maximization of the v(S)
            coal_payoff, argmaxs = calculate_tot_coal_payoff(configuration)
            #we store payoffs and the values that optimize the total coalition's payoff
            coal_payoffs.append(coal_payoff)
            argmaxs_list.append(argmaxs)
            payoff_vector = calculate_payoff_vector()
        properties_list = verify_properties()






    def generate_load():

        return res


    def player_utility
