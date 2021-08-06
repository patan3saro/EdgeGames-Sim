import numpy as np
import math
from game import Game

#by default player 0 is the NO
#Players number is mandatory
def main(players_number=3, rt_players=None, p_cpu=None, T_horizon=None, type_slot_t=None):
    game=Game()
    # feasible permutation are 2^(N-1)-1 instead of 2
    #each coalition element is a tuple player = (id, type)
    all_players_tuple = []
    coalitions=game.feasible_permutations(players_number, rt_players)
    # Config manual or automatic
    #automatic --> combinatorial configurations
    if p_cpu==None or T_horizon==None or type_slot_t==None:
        configurations = game.generate_configs()
    #manual --> only one configuration
    else:
        configurations = [(p_cpu, T_horizon)]

    for configuration in configurations:
        # list of all the payoff for different coalitions
        coal_payoffs = []
        argmaxs_list = []
        p_cpu, T_horizon= configuration
        for coalition in coalitions:
            #preparing parameters to calculate payoff
            params = (p_cpu, T_horizon, coalition)
            game.set_params(params)
            #total payoff is the result of the maximization of the v(S)
            sol = game.calculate_coal_payoff()
            #we store payoffs and the values that optimize the total coalition's payoff
            #coal_payoffs.append(coal_payoff)
            #argmaxs_list.append(argmaxs)
            #payoff_vector = calculate_payoff_vector()
        #properties_list = verify_properties()

if __name__=='__main__':
    #players_number=int(input("Insert players' number"))
    main()