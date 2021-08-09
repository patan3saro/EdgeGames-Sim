import numpy as np
import math
from game import Game

#by default player 0 is the NO
#Players number is mandatory
def main(players_number=3, rt_players=None, p_cpu=0.05, T_horizon=1, type_slot_t="min"):
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
    # to know which is the best coalition among
    # all the coalition for all the configurations
    best_of_the_best_coal={}
    best_max_payoff=0
    for configuration in configurations:
        infos_all_coal_one_config=[]
        best_coalition={}
        max_payoff=0
        p_cpu, T_horizon= configuration
        for coalition in coalitions:
            #preparing parameters to calculate payoff
            params = (p_cpu, T_horizon, coalition)
            game.set_params(params)
            #total payoff is the result of the maximization of the v(S)
            sol = game.calculate_coal_payoff()
            #we store payoffs and the values that optimize the total coalition's payoff
            #remember that we minimize so maximum is the opposite
            coal_payoff= - sol['fun']
            #print(coal_payoff)
            optimal_decision = sol['x']
            info_dict = {"configuration": {
                "cpu_price_mCore": configuration[0],
                "horizon": configuration[1]
            }, "coalition": coalition,
                         "coalitional_payoff": coal_payoff,"optimal_variables": {
                    "capacity": optimal_decision[0],
                    "resources1": optimal_decision[1],
                    "resources2": optimal_decision[2]
                }}
            #keeping the best coalition for a given configuration
            if coal_payoff > max_payoff:
                best_coalition=info_dict
                max_payoff=coal_payoff
            infos_all_coal_one_config.append(info_dict)
            print(info_dict)
            if(game.is_convex(infos_all_coal_one_config)):
                print("Shapley value is in the core\n")
        #properties_list = verify_properties()
        #print(infos_all_coal_one_config[0])
        tmp_payoff=best_coalition["coalitional_payoff"]
        if tmp_payoff > best_max_payoff:
            best_of_the_best_coal = best_coalition
            best_max_payoff = tmp_payoff
    import json
    #print(json.dumps(best_of_the_best_coal, indent=4))

if __name__=='__main__':
    #players_number=int(input("Insert players' number"))
    main()