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
        return perms

    # we can provide the number of config to try
    # inputs: type of slots, it can be seconds or minutes
    #realistic time horizon of a cpu
    def generate_configs(self, max_config_number=15, type_slot='min', years_horizon=3):
        # available time horizons
        configurations = []
        one_year_minutes = 525600
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
        #Warning: SISTEMA QUESTA COSA CONSIDERANDO CHE POI GLI USERS POSSONO INSERIRLA!!!!
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

    def _1_player_utility_t(self, resources, player_type):
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

    def _2_player_utility_t(self, resources, player_type):
        # if a real time SP, e.g. Peugeot
        if player_type == "rt":
            #used to convert load in mCore
            conversion_factor=20
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
            #used to convert load in mCore
            conversion_factor=5
            # gets less benefit
            a = 4
            #we must generate a load that is comparable
            # with the curve of the load benefit _g
            #e.g. choose eta=height_of_g/1.1
            # eta and sigma must be positive and eta >= sigma/2
            eta = 200
            sigma = 50
            load = self._generate_load(eta, sigma)
        #benefit factor dollars per mCore per minute
        #see: https://edge.network/en/pricing/
        beta=0.007/(60*4000)
        #converting load in needed resources
        converted_load= load*conversion_factor
        #the utility saturate if converted load>resources
        variable=min(converted_load, resources)
        return beta*conversion_factor*variable


    # to calculate the coalitional utility we simulate intervals

    def coal_payoff_objective_function(self, x):
        #I get in this way the parameters because the signature of
        # the objective func must be like this
        p_cpu, T_horizon, coalition, _ , simulation_type = self.get_params()
        capacity = x[0]
        resources = x[1:]
        tot_utility = 0
        #if the network operator is not in the coalition or It is alone
        if (0, 'NO') not in coalition or ((0, 'NO'), )==coalition :
            return 0
        if simulation_type=="real":
            utility_f = self._2_player_utility_t
        else:
            utility_f = self._1_player_utility_t

        # we calculate utility function at t for a player only for SPs
        # coalition is a tuple that specify the type of player also
        for player in coalition[1:]:
            utility_time_sum = 0
            for t in range(T_horizon):
                # remember that resources is a vector
                player_type = player[1]
                utility_time_sum = utility_time_sum + utility_f(resources[player[0]-1], player_type)
            tot_utility = tot_utility + utility_time_sum
        #we use minimize function, so to maximize we minimize the opposite

        return -(tot_utility - p_cpu * capacity)

    # OPTIMIZATION
    def constraint1(self, x):
        players_number=self.get_params()[3]
        eq=x[0]
        for i in range(players_number-1):
            eq-=x[i+1]
        return  eq

    # max payoff computation
    def calculate_coal_payoff(self):
        con1 = {'type': 'eq', 'fun': self.constraint1}
        cons = [con1]
        players_number = self.get_params()[3]
        x0=[1000]
        for i in range(players_number-1):
            x0.append(x0[0]/players_number)
        #I bound the capacity: first item in tuple
        bnds = ((0, None),) * players_number
        sol = minimize(self.coal_payoff_objective_function, x0 , bounds=bnds, method='SLSQP', constraints=cons)
        return sol

    #Checking properties


    # Combinatory analisys => N*(N-1)/2
    #Valid only if we consider the coalition with NO
    def is_convex(self, coalitions_infos):
        convexity=[]
        for i in range(len(coalitions_infos)):
            for j in (range(i+1, len(coalitions_infos))):
                coal1=coalitions_infos[i]["coalition"]
                coal2=coalitions_infos[j]["coalition"]
                coal1_value=coalitions_infos[i]["coalitional_payoff"]
                coal2_value=coalitions_infos[j]["coalitional_payoff"]
                # searching for the union and intersection coalition
                union=tuple(set(coal1).union(coal2))
                intersection=tuple(set(coal1).intersection(coal2))

                if (0, 'NO') not in union:
                    convexity.append(True)
                else:
                    # empty intersection or with no NO
                    if (0,'NO') not in intersection:
                        intersection_value=0
                    elif (0,'NO') in intersection:
                            #search intersection
                            for k in coalitions_infos:
                                if(k["coalition"]==intersection):
                                    intersection_value=k["coalitional_payoff"]
                                if(k["coalition"]==union):
                                    union_value=k["coalitional_payoff"]
                                    #round values for the comparison
                                    if(round(union_value)>=round(coal1_value+coal2_value-intersection_value)):
                                        convexity.append(True)
                                    else:
                                        convexity.append(False)

        return False not in convexity

    def shapley_value_payoffs(self, best_coalition, infos_all_coal_one_config, players_number, coalitions):
        coalition_players_number=len(best_coalition)
        x_payoffs=[]
        N_factorial=math.factorial(players_number)
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
                for l in coalitions_dict_with_i:
                    if tuple(set(S["coalition"]).symmetric_difference(l["coalition"]))==(player,):
                        contribution = l["coalitional_payoff"] - S["coalitional_payoff"]
                        tmp=math.factorial(len(S["coalition"]))*math.factorial(players_number-len(S["coalition"])-1)*contribution
                        summation = summation + tmp
            x_payoffs.append((1/N_factorial)*summation)

        return x_payoffs
    # GETTERS AND SETTERS
    # to get parameters p_cpu, T_horizon, coalition, players_number
    def get_params(self):
        return self.params

    def set_params(self, params):
        self.params = params
