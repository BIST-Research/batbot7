#
# Author: Ben Westcott
# Date Created: 1/5/23
#

import os, sys
sys.path.append("../")

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

from threading import Thread
from queue import Queue

import test_queues
   
if __name__ == '__main__':
    
    write_queue = Queue(maxsize=1000)
    write_exit = False
    
    #run_queue = Queue(maxsize=1000)
    run_queue, nruns, interval = test_queues.long_test_no_mic()
    data_queue = Queue(maxsize=1000)
    sonar_exit = False
        
    #queue_item_ex = (data, suffix, save_path)
    
    bat_log = bb_log.get_log()
    
    dc = DataController('test_bat_conf.yaml', bat_log)
    
    sonar_m4 = m4.M4(dc.get_sonar_boards(), dc.get_sonar_baud(), bat_log)
    sc = SonarController(sonar_m4, bat_log)
        
    t_write = DataThread(write_queue, (lambda : write_exit))
    t_sonar = SonarThread(run_queue, data_queue, sc, (lambda : sonar_exit))
    
    save_path = dc.create_run_dir()
    nidx = 1
    
    full_save_path = f"{dc.get_data_directory()}/{save_path}"
    
    t_write.start()
    t_sonar.start()
    
    t_start = time.time()
        
    while nidx < nruns + 1:
        
        if not data_queue.empty():
            data, t = data_queue.get()
            write_queue.put((data, t, full_save_path, write_npy_fun))
            data_queue.task_done()
            nidx += 1
            
            if nidx % interval == 0:
                bat_log.info(f"[Sonar] got run {nidx}. took {time.time() - t_start}")
                t_start = time.time()
            
    sonar_exit = True
    write_exit = True
    t_sonar.join()
    t_write.join()
    bat_log.info(f"[Sonar] done.")    
    
        
    
