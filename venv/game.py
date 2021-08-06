import math
from itertools import chain, combinations
from scipy.optimize._minimize import minimize
import numpy as np


class Game:

    def _all_permutations(self, iterable):
        "all_permutation([0,1,2]) --> () (0,) (1,) (2,) (0,1) (0,2) (1,2) (0,1,2)"
        s = list(iterable)
        return list(chain.from_iterable(combinations(s, r) for r in range(len(s) + 1)))

    def feasible_permutations(self, players_number, rt_players):
        set_players = []

        if rt_players == None:
            #one half rt and the other half nrt
            rt_players=round((players_number-1)/2)
        #assign type to players
        for i in range(players_number):
            #valid only for SPs
            # SPs NRT
            if i!=0 and rt_players>0:
                set_players.append((i, "rt"))
                rt_players-=1
            #SPs NRT
            elif i!=0:
                set_players.append((i, "nrt"))
            #NO
            else:
                set_players.append((i, "NO"))

        perms = self._all_permutations(set_players)
        feasible_perms = []
        # to exclude the coalition with just the NO and empty coalition we start from index 2
        for perm in perms[2:]:
            if 0 in perm[0]:
                feasible_perms.append(perm)
        return feasible_perms

    # we can provide the number of config to try
    # inputs: type of slots, it can be seconds or minutes
    #realistic time horizon of a cpu
    def generate_configs(self, max_config_number=15, type_slot='min', years_horizon=3):
        # available time horizons
        configurations = []
        one_year_minutes = 5 # 525600
        one_year_seconds = 3.154e+7
        T_horizon_avail = []
        if type_slot == "sec":
            t = one_year_seconds
        elif type_slot == "min":
            t = one_year_minutes
        for i in range(years_horizon):
            T_horizon_avail.append(t * (i+1))
        # available cpu prices per mCore
        # obs: realistic prices e.g. based on commercial expensive CPUs
        p_cpu_list = [0.05, 0.1, 0.15, 0.2, 0.25,0.3, 0.35, 0.4]
        # it generates all the combination M*N where M,N are the lengths of the two lists
        # these combinations are
        gen = ((x, y) for x in p_cpu_list for y in T_horizon_avail)
        # configurations is a list of tuples
        for u, v in gen:
            configurations.append((u, v))
        # we return the maximum number allowed of configs
        #SISTEMA QUESTA COSA CONSIDERANDO CHE POI GLI USERS POSSONO INSERIRLA!!!!
        return configurations[:min(max_config_number,len(configurations))]

    # useful functions to create the utility at time t for each player
    def _f(self, resources, a):
        #we must saturate the number of resources to obtain  solution>=0
        #in fact one of the intersection with axis x (y=0) is in x=0 --> y=0
        #the other one is in x=2a+100 (found solving the equation)
        #h determines the spread of the curve
        # and we need a great spread because the number of resources
        # can be in the order of 10^3 or 10^4
        h = 0.00001
        resources = min(resources, (2*a+(1/h)))
        #resources is by default > 0 thanks to the bounds in minimize function
        #so we will have always _f>=0
        return (h * (a ** 2) + resources - h * (resources - a) ** 2)

    def _g(self, load):
        # h (height) determine the saturation value
        h=200
        #this lowers the function
        l=2
        #determines the slope og the function
        s=0.03
        #m moves to the right  if >0 else to the left the function
        m=6
        return (h / (1 + math.e ** (- (load*s - m)))) - l

    # this function generates load randomly
    def _generate_load(self, eta, sigma):
        # WARNING: randomness generates problems with the optimization
        tmp = 50 # np.random.randint(eta - sigma/2, eta + sigma/2)
        return tmp

    def _player_utility_t(self, resources, player_type):
        # if a real time SP, e.g. Peugeot
        if player_type == "rt":
            # gets a great benefit from resources at the edge with this a
            a = 10
            #we must generate a load that is comparable
            # with the curve of the load benefit _g
            #e.g. choose eta=height_of_g/1.2
            # eta and sigma must be positive and eta >= sigma/2
            eta = 300
            sigma = 80
            load = self._generate_load(eta, sigma)
        # if not real time SP, e.g. Netflix
        else:
            # gets less benefit
            a = 4
            #we must generate a load that is comparable
            # with the curve of the load benefit _g
            #e.g. choose eta=height_of_g/1.1
            # eta and sigma must be positive and eta >= sigma/2
            eta = 200
            sigma = 50
            load = self._generate_load(eta, sigma)
        return self._f(resources, a) * self._g(load)

    # to calculate the coalitional utility we simulate intervals

    def coal_payoff_objective_function(self, x):
        #I get in this way the parameters because the signature of
        # the objective func must be like this
        p_cpu, T_horizon, coalition = self.get_params()
        capacity = x[0]
        resources = x[1:]
        tot_utility = 0
        # we calculate utility function at t for a player only for SPs
        # coalition is a tuple that specify the type of player also
        for player in coalition[1:]:
            utility_time_sum = 0
            for t in range(T_horizon):
                # remember that resources is a vector
                player_type = player[1]
                utility_time_sum = utility_time_sum + self._player_utility_t(resources[player[0]-1], player_type)
            tot_utility = tot_utility + utility_time_sum
        #we use minimize function, so to maximize we minimize the opposite
        return -(tot_utility - p_cpu * capacity)

    # OPTIMIZATION
    def constraint1(self, x):
        return x[0] - x[1] - x[2]

    # max payoff computation
    def calculate_coal_payoff(self):
        con1 = {'type': 'eq', 'fun': self.constraint1}
        cons = [con1]
        x0=[1000, 500, 500]
        b=(1, None)
        #I bound the capacity: first item in tuple
        bnds=((0, None),b,b)
        sol = minimize(self.coal_payoff_objective_function, x0 , bounds=bnds, method='SLSQP', constraints=cons)
        return sol

    # GETTERS AND SETTERS

    # to get parameters like p_cpu, coalition etc
    def get_params(self):
        return self.params

    def set_params(self, params):
        self.params = params
