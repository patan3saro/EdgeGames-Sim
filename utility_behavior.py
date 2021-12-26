import math

import matplotlib.pyplot as plt
import numpy as np


def _utility_i(beta_i, h_i, load_t, csi=0.06, s=0.5):
    # return beta_i * pow(h_i, csi / s) * pow(load_t, csi)
    return beta_i * load_t * (1 - math.exp(-csi * h_i))


list_h = []
list_ut = []
list_load = []

for h in range(100):
    list_h.append(h)
    list_ut.append(_utility_i(0.5, h, 15000))

plt.figure()
plt.plot(list_h, np.array(list_ut), '--bo')
plt.xlabel('h')
plt.ylabel('utility')
plt.draw()

list_ut = []
list_load = []
h = 10
load = 500
for load in range(100):
    list_load.append(load)
    list_ut.append(_utility_i(0.5, h, load))
    load += 100

plt.figure()
plt.plot(list_load, np.array(list_ut), '--bo')
plt.xlabel('load')
plt.ylabel('utility')
plt.draw()

plt.show()
