from game import Game
import json


# by default player 0 is the NO
# Players number is mandatory
# simulation_type
def main(players_number=2, simulation_type="real", rt_players=None, p_cpu=0.004, horizon=3, type_slot_t="min"):
    game = Game()
    # feasible permutation are 2^(N-1)-1 instead of 2
    # each coalition element is a tuple player = (id, type)
    coalitions = game.feasible_permutations(players_number, rt_players)
    # Config manual or automatic
    # automatic --> combinatorial configurations
    if p_cpu is None:
        configurations = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4]
    # manual --> only one configuration
    else:
        configurations = [p_cpu]
    if type_slot_t == "min":
        T_horizon = horizon * 525600
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
        best_coalition = {}
        max_payoff = -0.1
        p_cpu = configuration
        # we exclude the empty coalition
        for coalition in coalitions:
            # preparing parameters to calculate payoff
            params = (p_cpu, T_horizon, coalition, len(coalition), simulation_type)
            game.set_params(params)
            # total payoff is the result of the maximization of the v(S)
            sol = game.calculate_coal_payoff()
            # we store payoffs and the values that optimize the total coalition's payoff
            # remember that we minimize so maximum is the opposite
            coal_payoff = - sol['fun']
            # computation of the payoff_vector
            payoffs_vector = game.calculate_payoff_vector(coal_payoff, coalition, players_number)
            optimal_decision = tuple(sol['x'])
            coal_payoff_second_game = game.calculate_coal_payoff_second_game(optimal_decision)
            info_dict = {"configuration": {
                "cpu_price_mCore": configuration,
                "horizon": horizon
            }, "coalition": coalition,
                "coalitional_payoff": coal_payoff,
                "second_game_coalitional_payoff": coal_payoff_second_game,
                "optimal_variables": optimal_decision,
                "payoffs_vector": payoffs_vector
            }
            # keeping the best coalition for a given configuration
            infos_all_coal_one_config.append(info_dict)

        best_coalition = game.best_coalition(infos_all_coal_one_config)
        all_infos.append(infos_all_coal_one_config)
        tmp_payoff = best_coalition["coalitional_payoff"]

        if tmp_payoff > best_max_payoff:
            best_of_the_best_coal = best_coalition
            best_max_payoff = tmp_payoff
    # choosing info of all coalition for the best config
    for elem in all_infos:
        if best_of_the_best_coal in elem:
            infos_all_coal_one_config = elem
    print(json.dumps(best_of_the_best_coal, indent=4))
    games_payoff_vectors = []
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


if __name__ == '__main__':
    # players_number=int(input("Insert players' number"))
    main()
