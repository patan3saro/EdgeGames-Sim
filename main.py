from game import Game
import utils


# by default player 0 is the NO
# Players number is mandatory
# simulation_type
def main(players_number=3, simulation_type="real", rt_players=None, p_cpu=0.05, horizon=1, type_slot_t="min",
          beta = 0.5):
    game = Game()
    # feasible permutation are 2^(N-1)-1 instead of 2
    # each coalition element is a tuple player = (id, type)
    coalitions = utils.feasible_permutations(players_number, rt_players)
    grand_coalition = coalitions[-1]
    # Config manual or automatic
    # automatic --> combinatorial configurations
    if p_cpu is None:
        configurations = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4]
    # manual --> only one configuration
    else:
        configurations = [p_cpu]
    if type_slot_t == "min":
        T_horizon = horizon * 2  # 525600
    elif type_slot_t == "sec":
        T_horizon = horizon * 3.154e+7
    else:
        print("Type of time slot not allowed\n")
    # to know which is the best coalition among
    # all the coalition for all the configurations
    best_of_the_best_coal = {}
    best_max_payoff = -1
    all_infos = []

    game_type = ("first", "second")
    for configuration in configurations:
        infos_all_coal_one_config = []
        all_coal_payoffs = []
        all_coal_payoffs_second = []
        best_coalition = {}
        max_payoff = -0.1
        p_cpu = configuration
        # we exclude the empty coalition
        for coalition in coalitions[1:]:
            # preparing parameters to calculate payoff
            params = (p_cpu, T_horizon, coalition, len(coalition), simulation_type, beta, players_number)
            game.set_params(params)
            # total payoff is the result of the maximization of the v(S)
            sol, payoffs_vector, capacity, coal_payoff_second_game, payoffs_vector_second_game \
                = game.calculate_coal_payoff()
            # we store payoffs and the values that optimize the total coalition's payoff
            coal_payoff = sol['fun']
            print(coalition, coal_payoff, payoffs_vector)
            info_dict = {"configuration": {
                "cpu_price_mCore": configuration,
                "horizon": horizon
            }, "coalition": coalition,
                "coalitional_payoff": coal_payoff,
                "second_game_coalitional_payoff": coal_payoff_second_game,
                "capacity": capacity,
                "core": payoffs_vector
            }
            # keeping the best coalition for a given configuration
            infos_all_coal_one_config.append(info_dict)
            all_coal_payoffs.append(coal_payoff)
            all_coal_payoffs_second.append(coal_payoff_second_game)
            if coalition == grand_coalition:
                grand_coal_payoff = coal_payoff
                grandc_payoff_vec = payoffs_vector
                grand_coal_payoff_second = coal_payoff_second_game
                grandc_payoff_vec_second = payoffs_vector_second_game
        # verifing properties for 1st game
        check_first = game.verify_properties(all_coal_payoffs, grand_coal_payoff, grandc_payoff_vec, game_type="first")

        # verifing properties for 2nd game
        check_second = game.verify_properties(all_coal_payoffs_second, grand_coal_payoff_second,
        grandc_payoff_vec_second,  game_type="second")
        if check_first and check_second:
            print("Capacity:", capacity, "mCore")
            print("Coalition net incomes:", grand_coal_payoff)
            print("Coalition payment:", grand_coal_payoff_second - grand_coal_payoff)
            print("Players gross incomes:", grand_coal_payoff_second)
            print("Players net incomes:", grandc_payoff_vec)
            print("Players payment:", grandc_payoff_vec_second - grandc_payoff_vec)

        all_infos.append(infos_all_coal_one_config)
        tmp_payoff = 0  # best_coalition["coalitional_payoff"]

        # if tmp_payoff > best_max_payoff:
        #    best_of_the_best_coal = best_coalition
        #    best_max_payoff = tmp_payoff
    # choosing info of all coalition for the best config
    for elem in all_infos:
        if best_of_the_best_coal in elem:
            infos_all_coal_one_config = elem
    # print(best_of_the_best_coal)
    games_payoff_vectors = []


'''
    for q in game_type:
        print("Checking if the", q, "game is convex...\n")
        if game.is_convex(infos_all_coal_one_config, q):
            print("The", q, "game is convex!\n")
            players_payoffs = game.shapley_value_payoffs(best_of_the_best_coal, infos_all_coal_one_config,
                                                         players_number,
                                                         coalitions, q)
            games_payoff_vectors.append(players_payoffs)
            print("Shapley value is in the core:", players_payoffs, "\n")
            print("Checking if the payoff is efficient...")
            # we don'nt consider the exact difference but a little tolerance
            # since there are approx errors
            # if game.is_efficient():
            #    print("The payoff is efficient\n")
            # else:
            #    print("The payoff is not efficient\n")
        else:
            print("The game is not convex!\n")
    print("Each player pay:\n")
    print(game.how_much_must_pay(games_payoff_vectors))
'''

if __name__ == '__main__':
    # players_number=int(input("Insert players' number"))
    main()
