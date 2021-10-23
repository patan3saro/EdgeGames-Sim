import numpy as np
from game import Game
import utils
import os, psutil
import time
import matplotlib.pyplot as plt


# by default player 0 is the NO
# Players number is mandatory
def main(players_number=3, rt_players=None, p_cpu=0.05, horizon=4*365, type_slot_t="min",
         beta=0.5, chi=0, alpha=0.5, HC=100000000, gamma=10, eta=1000 * 15,
         heterogeneity_betas=False, heterogeneity_gammas=False, heterogeneity_etas=False):
    start = time.time()

    # setto beta per ogni service provider
    if heterogeneity_betas:
        betas = [(8 / 5) * beta, (2 / 5) * beta]
    else:
        betas = [beta] * 2

    if heterogeneity_gammas:
        gammas = [(8 / 5) * gamma, (2 / 5) * gamma]
    else:
        gammas = [gamma] * 2

    if heterogeneity_etas:
        loads = [(8 / 5) * eta, (2 / 5) * eta]
    else:
        loads = [eta] * 2

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
        T_horizon = 96
    elif type_slot_t == "sec":
        T_horizon = horizon * 3.154e+7
    else:
        print("Type of time slot not allowed\n")
    # to know which is the best coalition among
    # all the coalition for all the configurations
    best_of_the_best_coal = {}
    all_infos = []
    payoff_vector = []
    configurations = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.1, 1.2, 1.3, 1.5]
    y_axis_cpu_capacity = []
    y_axis_px_NO = []
    y_axis_pr_NO = []
    y_axis_pp_NO = []
    y_axis_px_SP1 = []
    y_axis_pr_SP1 = []
    y_axis_pp_SP1 = []
    y_axis_px_SP2 = []
    y_axis_pr_SP2 = []
    y_axis_pp_SP2 = []
    y_coal_payoff = []

    for configuration in configurations:
        infos_all_coal_one_config = []
        all_coal_payoffs = []
        p_cpu = configuration
        # we exclude the empty coalition
        for coalition in coalitions[1:]:
            # preparing parameters to calculate payoff
            params = (
                p_cpu, T_horizon, coalition, len(coalition), beta, players_number, chi, alpha, HC, betas,
                gammas, loads, horizon)
            game.set_params(params)
            # total payoff is the result of the maximization of the v(S)
            sol = game.calculate_coal_payoff()
            if coalition == coalitions[-1]:
                PIPPO = sol['x'][-1] * p_cpu
                resources_alloc = sol['x']
            # we store payoffs and the values that optimize the total coalition's payoff
            coal_payoff = -sol['fun']
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

        y_coal_payoff.append(grand_coal_payoff)

        # choosing info of all coalition for the best config
        payoff_vector = game.shapley_value_payoffs(infos_all_coal_one_config,
                                                   players_number,
                                                   coalitions)
        y_axis_px_NO.append(payoff_vector[0])
        y_axis_px_SP1.append(payoff_vector[1])
        y_axis_px_SP2.append(payoff_vector[2])

        print("Shapley value is in the core, the fair payoff is:", payoff_vector, "\n")
        # Further verification of the solution (payoff vector) in the core
        # check_core = game.verify_properties(all_coal_payoffs, grand_coal_payoff, payoff_vector)

        if True:
            print("Coalition net incomes:", grand_coal_payoff)
            print("Capacity:", sol['x'][-1], "\n")
            y_axis_cpu_capacity.append(sol['x'][-1])
        all_infos.append(infos_all_coal_one_config)

        print("Each player pay:\n")

        print("Proceeding with calculation of revenues vector and payments\n")
        res = game.how_much_rev_paym(payoff_vector, sol['x'])
        y_axis_pr_NO.append(res[0][0])
        y_axis_pr_SP1.append(res[0][1])
        y_axis_pr_SP2.append(res[0][2])

        y_axis_pp_NO.append(res[1][0])
        y_axis_pp_SP1.append(res[1][1])
        y_axis_pp_SP2.append(res[1][2])

        print("Revenue array:", res[0], "\n")
        print("Payment array:", res[1], "\n")
        if abs(PIPPO - sum(res[1])) > 0.01:
            print("ERROR: the sum of single payments (for each players) doesn't match the  ", PIPPO , sum(res[1]))
        else:
            print("Total payment and sum of single payments are equal!\n")

        print("Total memory used by the process: ", psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2, "MB")
        print("Time required for the simulation: ", round(time.time() - start), "seconds")
        # print capacity and p_cpu
    plt.figure()
    plt.plot(np.array(configurations)/beta, y_axis_cpu_capacity)
    plt.xlabel('P_Cpu/Beta (adimensional)')
    plt.ylabel('Cpu\'s Capacity (milliCore)')
    plt.draw()

    plt.figure()
    plt.plot(np.array(configurations)/beta, y_coal_payoff)
    plt.xlabel('P_Cpu/Beta (adimensional)')
    plt.ylabel('Coalitional payoff ($)')
    plt.draw()

    plt.figure()
    plt.plot(np.array(configurations)/beta, y_axis_px_NO, color="blue", label="net benefit")
    plt.plot(np.array(configurations)/beta, y_axis_pr_NO, color="red", label="gross benefit")
    plt.plot(np.array(configurations)/beta, y_axis_pp_NO, color="orange", label="payment")
    plt.xlabel('P_Cpu/Beta (adimensional)')
    plt.ylabel('Payoff NO ($)')
    plt.legend()
    plt.draw()

    plt.figure()
    plt.plot(np.array(configurations)/beta, y_axis_px_SP1, color="blue", label="net benefit")
    plt.plot(np.array(configurations)/beta, y_axis_pr_SP1, color="red", label="gross benefit")
    plt.plot(np.array(configurations)/beta, y_axis_pp_SP1, color="orange", label="payment")
    plt.xlabel('P_Cpu/Beta (adimensional)')
    plt.ylabel('Payoff SP1 rt ($)')
    plt.legend()
    plt.draw()

    plt.figure()
    plt.plot(np.array(configurations)/beta, y_axis_px_SP2, color="blue", label="net benefit")
    plt.plot(np.array(configurations)/beta, y_axis_pr_SP2, color="red", label="gross benefit")
    plt.plot(np.array(configurations)/beta, y_axis_pp_SP2, color="orange", label="payment")
    plt.xlabel('P_Cpu/Beta (adimensional)')
    plt.ylabel('Payoff SP2 nrt ($)')
    plt.legend()
    plt.draw()

    plt.show()


if __name__ == '__main__':
    # players_number=int(input("Insert players' number"))
    main()
