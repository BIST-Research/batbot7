import os, sys
import numpy as np
import time

sys.path.append("../")

from bb_sonar import determine_timer_vals
from bb_sonar import generate_chirp

def time_timer_fun(it):

    trange = np.linspace(0.5E-6, 0.5, it)
    lst = []
    for n in trange:
        start = time.time()
        determine_timer_vals(n)
        end = time.time()
        lst.append(end - start)
    return sum(lst)/it
        

def time_chirp_fun(it):
    T_max = 65E-3 #sec
    N_max = 65E3
    
    T_min = 1E-3 #sec
    N_min = 1E3
    
    trange = np.linspace(T_min, T_max, it)
    nrange = np.linspace(N_min, N_max, it)
    
    f0 = 120E3 #Hz
    f1 = 20E3 #Hz
    Ts = 1E-6 #sec
    method = 'linear'
    window = 'hann'
    
    lst = []
    
    for n, k in zip(trange, nrange):
        start = time.time()
        generate_chirp(f0, f1, n, k, Ts, method, window)
        end = time.time()
        lst.append(end - start)
    return sum(lst)/it

if __name__ == '__main__':
    
    # avg = 2.45 usec
    print(time_timer_fun(it=1000))
    # avg = 1.55 msec
    print(time_chirp_fun(it=1000))
    
    
    
    
