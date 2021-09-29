from game import Game
import utils
import os, psutil
import time


# by default player 0 is the NO
# Players number is mandatory
def main(players_number=3, rt_players=None, p_cpu=0.05, horizon=1, type_slot_t="min",
         beta=0.5, chi=-0.9, alpha=0.5, HC=100000000):
    start = time.process_time()
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
    all_infos = []
    payoff_vector = []
    PIPPO = 0

    game_type = ("first", "second")
    for configuration in configurations:
        infos_all_coal_one_config = []
        all_coal_payoffs = []
        p_cpu = configuration
        # we exclude the empty coalition
        for coalition in coalitions[1:]:
            # preparing parameters to calculate payoff
            params = (p_cpu, T_horizon, coalition, len(coalition), beta, players_number, chi, alpha, HC)
            game.set_params(params)
            # total payoff is the result of the maximization of the v(S)
            sol = game.calculate_coal_payoff()
            if coalition == coalitions[-1]:
                PIPPO = sol['x'][-1] * p_cpu
                resources_alloc = sol['x']
            # we store payoffs and the values that optimize the total coalition's payoff
            coal_payoff = -sol['fun']
            print("Payoff: ", coal_payoff, "coalition", coalition)
            info_dict = {"configuration": {
                "cpu_price_mCore": configuration,
                "horizon": horizon
            }, "coalition": coalition,
                "coalitional_payoff": coal_payoff,
            }
            # keeping the best coalition for a given configuration
            infos_all_coal_one_config.append(info_dict)
            all_coal_payoffs.append(coal_payoff)
            if coalition == grand_coalition:
                grand_coal_payoff = coal_payoff

        # we get the entire core
        payoff_vector = game.calculate_core(infos_all_coal_one_config)
        # Further verification of the solution (payoff vector) in the core
        check_first = game.verify_properties(all_coal_payoffs, grand_coal_payoff, payoff_vector)

        if check_first:
            print("Coalition net incomes:", -grand_coal_payoff)
            print("Capacity:", sol['x'][-1], "\n")
        all_infos.append(infos_all_coal_one_config)

    # choosing info of all coalition for the best config

    print("Checking if the game is convex...\n")
    if game.is_convex(infos_all_coal_one_config):
        print("The game is convex!\n")
        payoff_vector = game.shapley_value_payoffs(infos_all_coal_one_config,
                                                   players_number,
                                                   coalitions)

        print("Shapley value is in the core, the fair payoff is:", payoff_vector, "\n")

    else:
        print("The game is not convex!\n")
        print("A solution in the core (not fair) is the result \n"
              "of the system of inequalities:", payoff_vector, "\n")
    print("Each player pay:\n")

    print("Proceeding with calculation of revenues vector and payments\n")
    res = game.how_much_rev_paym(payoff_vector, sol['x'], 0)
    print("Revenue array:", res[0], "\n")
    print("Payment array:", res[1], "\n")
    if abs(PIPPO - sum(res[1])) > 0.001:
        print("ERROR: the sum of single payments (for each players) doesn't match the  ")
    else:
        print("Total payment and sum of single payments are equal!\n")

    print("Total memory used by the process: ", psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2, "MB")
    print("Time required for the simulation: ", time.process_time() - start, "seconds")


if __name__ == '__main__':
    # players_number=int(input("Insert players' number"))
    main()
