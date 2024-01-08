#
# Author: Ben Westcott
# Date Created: 1/8/23
#

import os, sys
import numpy as np
import time
import bb_log
import m4
import yaml
import time

from bb_sonar import determine_timer_vals
from bb_sonar import generate_chirp
from bb_sonar import check_partition
from bb_sonar import determine_chunk_count
from bb_sonar import SonarController
from bb_sonar import part_default
from bb_sonar import SonarThread

from bb_data import DataThread
from bb_data import write_npy_fun

from bb_utils import bin2dec
from bb_data import DataController

from hw_defs import *

from threading import Thread
from queue import Queue

def update_bounds(t_min, t_max, value):
    
    if value < t_min:
        t_min = value
    
    if value > t_max:
        t_max = value
    
    return t_min, t_max
    
def metric_out_str(name, t_avg, t_min, t_max):
    return f"{name}:\n\t\tavg\t\t{t_avg}\n\t\tmin\t\t{t_min}\n\t\tmax\t\t{t_max}\n"

if __name__ == '__main__':
    
    bat_log = bb_log.get_log()
        
    dc = DataController('test_bat_conf.yaml', bat_log)
    d = dc.create_run_dir(prefix="metric")
    
    sonar_m4 = m4.M4(dc.get_sonar_boards(), dc.get_sonar_baud(), bat_log)
    sc = SonarController(sonar_m4, bat_log)
    
    it = 10000
    sc.enter_update()
    sc.buffer_update(0, 64, 0)
    
    T_wait = 1E-6
    sc.wait_timer_update(T_wait)
    sc.exit_update()
    
    t_base = (0, 0, 0, 200)
    
    t_run, t_run_total, t_run_max, t_run_min = t_base
    
    print("Testing run timings...")
    
    n=0
    while True:
    
        if n >= it:
            break
                
        if not sc.is_running():
            sc.start_job(do_chirp=True)
            t_run = time.time()
            
        else:
            data = sc.get_job()
            if data is not None and type(data) is not bool:
            
                t_run = time.time() - t_run
                t_run_total += t_run
                
               # if n % 100 == 0:
               #     print(f"{n}\t\t{t_run}")
                
                t_run_min, t_run_max = update_bounds(t_run_min, t_run_max, t_run)
                n += 1
                
    t_run_avg = t_run_total/it
    t_serial_avg = t_run_avg - (T_wait + T_EXIT_TIMERS)
    t_serial_max = t_run_max - (T_wait + T_EXIT_TIMERS)
    t_serial_min = t_run_min - (T_wait + T_EXIT_TIMERS)
    
    print(metric_out_str("run", t_run_avg, t_run_min, t_run_max))
    print(metric_out_str("ser", t_serial_avg, t_serial_min, t_serial_max))

    t_enter, t_enter_total, t_enter_max, t_enter_min = t_base
    t_exit, t_exit_total, t_exit_max, t_exit_min = t_base
    t_buffer_upd, t_buffer_upd_total, t_buffer_upd_max, t_buffer_upd_min = t_base
    t_wait_upd, t_wait_upd_total, t_wait_upd_max, t_wait_upd_min = t_base
    
    for n in range(0, it):
        t_enter = time.time()
        sc.enter_update()
        t_enter = time.time() - t_enter
        
        t_enter_total += t_enter
        t_enter_min, t_enter_max = update_bounds(t_enter_min, t_enter_max, t_enter)
        
        t_exit = time.time()
        sc.exit_update()
        t_exit = time.time() - t_exit
        
        t_exit_total += t_exit
        t_exit_min, t_exit_max = update_bounds(t_exit_min, t_exit_max, t_exit)
        
        
    t_enter_avg = t_enter_total/it
    t_exit_avg = t_exit_total/it
    
    print("Testing update timings...")
    
    print(metric_out_str("enter", t_enter_avg, t_enter_min, t_enter_max))
    print(metric_out_str("exit", t_exit_avg, t_exit_min, t_exit_max))
    
    for n in range(0, it):
        sc.enter_update()
        t_buffer_upd = time.time()
        sc.buffer_update(3000, 10000, 10000)
        t_buffer_upd = time.time() - t_buffer_upd
        sc.exit_update()
        
        t_buffer_upd_total += t_buffer_upd
        t_buffer_upd_min, t_buffer_upd_max = update_bounds(t_buffer_upd_min, t_buffer_upd_max, t_buffer_upd)
        
    t_buffer_upd_avg = t_buffer_upd_total/it
    
    print(metric_out_str("buffer", t_buffer_upd_avg, t_buffer_upd_min, t_buffer_upd_max))

    for n in range(0, it):
        sc.enter_update()
        t_wait_upd = time.time()
        sc.wait_timer_update(1E-6)
        t_wait_upd = time.time() - t_wait_upd
        sc.exit_update()
        
        t_wait_upd_total += t_wait_upd
        t_wait_upd_min, t_wait_upd_max = update_bounds(t_wait_upd_min, t_wait_upd_max, t_wait_upd)
        
    t_wait_upd_avg = t_wait_upd_total/it
    
    print(metric_out_str("wait", t_wait_upd_avg, t_wait_upd_min, t_wait_upd_max))
    
    
                    
                    
                    
                
                
                
            
            

