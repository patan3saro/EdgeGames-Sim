import os
import psutil
import time

import matplotlib.pyplot as plt
import numpy as np

import utils
from game import Game

# years until the expiration of the CPU
years = 3
# maximum number of cores that the NO can host
max_cores_hosted = 4


# horizon is the number of days in years

def main(players_number=3, rt_players=None, price_cpu=1.5, horizon=years * 365, chi=0, alpha=0.5,
         HC=max_cores_hosted * 1000, avg_load=1000 * 15,
         heterogeneity_avg_benefit=True, heterogeneity_avg_load=False):
    # starting time to calculate the duration of the simulation
    start = time.time()
    game = Game()

    if not heterogeneity_avg_load:
        avg_loads_all_players = [avg_load] * 2
    else:
        avg_loads_all_players = [(8 / 5) * avg_load, (2 / 5) * avg_load]

    # each coalition element is a tuple player = (id, type)
    coalitions = utils.feasible_permutations(players_number, rt_players)
    # the last coalition is the Grand coalition, i.e. coalition considering all the players
    grand_coalition = coalitions[-1]

    # list to collect the values of:
    # CPU's capacity
    y_axis_cpu_capacity = []
    # px=net benefit, pr=gross benefit, pp=payment for the NO
    y_axis_px_NO = []
    y_axis_pr_NO = []
    y_axis_pp_NO = []
    # px=net benefit, pr=gross benefit, pp=payment for the SP1
    y_axis_px_SP1 = []
    y_axis_pr_SP1 = []
    y_axis_pp_SP1 = []
    # px=net benefit, pr=gross benefit, pp=payment for the SP2
    y_axis_px_SP2 = []
    y_axis_pr_SP2 = []
    y_axis_pp_SP2 = []
    y_coal_payoff = []
    # split of resources among the players
    resources_NO = []
    resources_SP1 = []
    resources_SP2 = []

    # timeslot is 15 minutes (96 in one day)
    daily_timeslots = 96

    # price_cpu_ammortized is the price of the CPU for each timeslot
    price_cpu_ammortized = price_cpu / (horizon * daily_timeslots)

    # is the average value of beta used to generate configurations
    beta_centr = price_cpu_ammortized

    configurations = [beta_centr / 5, beta_centr / 4, beta_centr / 3, beta_centr / 2, beta_centr, beta_centr,
                      2 * beta_centr, 3 * beta_centr, 4 * beta_centr, 5 * beta_centr, 6 * beta_centr, 7 * beta_centr,
                      8 * beta_centr]

    # for each value of beta in configurations (benefit factor)
    for configuration in configurations:
        infos_all_coal_one_config = []
        beta = configuration

        # setting beta for each Service Provider
        if not heterogeneity_avg_benefit:
            betas = [beta] * 2
        else:
            betas = [(8 / 5) * beta, (2 / 5) * beta]

        # we exclude the empty coalition
        for coalition in coalitions[1:]:
            # preparing parameters for the game
            params = (
                price_cpu, daily_timeslots, coalition, len(coalition), beta, players_number, chi, alpha, HC, betas,
                0, avg_loads_all_players, horizon)
            game.set_params(params)

            # total payoff is the result of the maximization of the objective function v(S)
            sol = game.calculate_coal_payoff()

            if coalition == coalitions[-1]:
                grand_coal_payment_one_config = sol['x'][-1] * price_cpu
                resources_alloc = sol['x']
            np.random.seed()
            # we store payoffs and the values that optimize the total coalition's payoff
            coal_payoff = -sol['fun']

            info_one_coalition_one_confing = {
                "beta": configuration,
                "coalition": coalition,
                "coalitional_payoff": coal_payoff,
            }

            # keeping the payoffs for each coalition to calculate the Shapley value
            # in fact, we need all the coalitional payoff
            infos_all_coal_one_config.append(info_one_coalition_one_confing)

            # keeping the grand coalitional payoff to plot how it changes
            if coalition == grand_coalition:
                grand_coal_payoff = coal_payoff

        # keeping the grand coalitional payoff to plot how it changes
        y_coal_payoff.append(grand_coal_payoff)

        # result of the game (payoffs' vector) calculated using Shapley value
        payoff_vector = game.shapley_value_payoffs(infos_all_coal_one_config,
                                                   players_number,
                                                   coalitions)

        # storing of payoff values for each player to plot them
        y_axis_px_NO.append(payoff_vector[0])
        y_axis_px_SP1.append(payoff_vector[1])
        y_axis_px_SP2.append(payoff_vector[2])

        print("Shapley value is (fair payoff vector):", payoff_vector, "\n")

        if True:
            print("Coalition net incomes:", grand_coal_payoff)
            print("Capacity:", sol['x'][-1], "\n")
            print("Resources split", sol['x'][:-1], "\n")
            # storing amount of cpu for each player
            resources_NO.append(sol['x'][0])
            resources_SP1.append(sol['x'][1])
            resources_SP2.append(sol['x'][2])
            # storing total cpu capacity
            y_axis_cpu_capacity.append(sol['x'][-1])

        print("Proceeding with calculation of revenues vector and payments\n")
        res = game.how_much_rev_paym(payoff_vector, sol['x'])

        # storing revenues for each player to plot
        y_axis_pr_NO.append(res[0][0])
        y_axis_pr_SP1.append(res[0][1])
        y_axis_pr_SP2.append(res[0][2])

        # storing payments for each player to plot
        y_axis_pp_NO.append(res[1][0])
        y_axis_pp_SP1.append(res[1][1])
        y_axis_pp_SP2.append(res[1][2])

        print("Revenues array:", res[0], "\n")
        print("Payments array:", res[1], "\n")

        # checking if the calculation of payments and revenues is correct
        print("Checking the correctness of the revenues and payments vectors...\n")

        if abs(grand_coal_payment_one_config - sum(res[1])) > 0.001:
            print("ERROR: the sum of single payments (for each players) don't match the total payment!")
        else:
            print("Total payment and sum of single payments are equal!\n")

        print("Total memory used by the process: ", psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2, "MB")
        print("Time required for the simulation: ", round(time.time() - start), "seconds")

    plt.figure()
    plt.plot(np.array(configurations) / price_cpu_ammortized, y_axis_cpu_capacity, '--bo')
    plt.xlabel('Beta_avg/P_Cpu')
    plt.ylabel('Cpu\'s Capacity (milliCore)')
    # plt.xscale('log')
    plt.ylim(ymin=0, ymax=max(y_axis_cpu_capacity) + 5)
    plt.draw()

    plt.figure()
    plt.plot(np.array(configurations) / price_cpu_ammortized, y_coal_payoff, '--bo')
    plt.xlabel('Beta_avg/P_Cpu')
    plt.ylabel('Coalitional payoff ($)')
    # plt.xscale('log')
    plt.draw()

    plt.figure()
    plt.plot(np.array(configurations) / price_cpu_ammortized, y_axis_px_NO, '--bo', color="blue", label="net benefit")
    plt.plot(np.array(configurations) / price_cpu_ammortized, y_axis_pr_NO, '--bo', color="red", label="gross benefit")
    plt.plot(np.array(configurations) / price_cpu_ammortized, y_axis_pp_NO, '--bo', color="orange", label="payment")
    plt.xlabel('Beta_avg/P_Cpu')
    plt.ylabel('Payoff NO ($)')
    plt.legend()
    plt.xscale('log')
    plt.draw()

    plt.figure()
    plt.plot(np.array(configurations) / price_cpu_ammortized, y_axis_px_SP1, '--bo', color="blue", label="net benefit")
    plt.plot(np.array(configurations) / price_cpu_ammortized, y_axis_pr_SP1, '--bo', color="red", label="gross benefit")
    plt.plot(np.array(configurations) / price_cpu_ammortized, y_axis_pp_SP1, '--bo', color="orange", label="payment")
    plt.xlabel('Beta_avg/P_Cpu')
    plt.ylabel('Payoff SP1 rt ($)')
    plt.legend()
    plt.xscale('log')
    plt.draw()

    plt.figure()
    plt.plot(np.array(configurations) / price_cpu_ammortized, y_axis_px_SP2, '--bo', color="blue", label="net benefit")
    plt.plot(np.array(configurations) / price_cpu_ammortized, y_axis_pr_SP2, '--bo', color="red", label="gross benefit")
    plt.plot(np.array(configurations) / price_cpu_ammortized, y_axis_pp_SP2, '--bo', color="orange", label="payment")
    plt.xlabel('Beta_avg/P_Cpu')
    plt.ylabel('Payoff SP2 nrt ($)')
    plt.legend()
    plt.draw()
    plt.xscale('log')

    plt.figure()
    labels = ['G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9', 'G10', 'G11', 'G12', 'G13']
    width = 0.35  # the width of the bars: can also be len(x) sequence

    plt.bar(labels, resources_NO, width, label='h_NO')
    plt.bar(labels, resources_SP1, width, label='h_SP1')
    plt.bar(labels, resources_SP2, width, label='h_SP2')

    plt.xlabel('Beta_avg/P_Cpu')
    plt.ylabel('Split of  (mCore)')
    plt.legend()
    plt.draw()

    plt.show()


if __name__ == '__main__':
    # players_number=int(input("Insert players' number"))
    main()
