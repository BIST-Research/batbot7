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

from bb_utils import bin2dec
from bb_data import DataController

from threading import Thread
from queue import Queue

import test_queues

class sonar_run(Thread):
    def __init__(self, run_queue, data_queue, sc, exit_cond):
        Thread.__init__(self)
        self.run_q = run_queue
        self.data_q = data_queue
        self.sc = sc
        self.exit_cond = exit_cond
        
    def run(self):
        RUN = 0x01
        UPDATE = 0x02
        curr_operation = None
        t_start = 0
        
        while True:
            
            if self.exit_cond() and self.run_q.empty():
                break
                
            if not self.run_q.empty() and curr_operation is None:
                update, do_chirp, wait_T, partition, chirp = self.run_q.get()
                
                if update:
                    curr_operation = UPDATE
                    # TODO: Should probably send an "update ready flag" from MCU
                    self.sc.enter_update()
                else:
                    curr_operation = RUN
                    self.sc.start_job(do_chirp=do_chirp)
                    t_start = time.time()
                    
            if curr_operation == RUN:
                if data := sc.get_job() is not None:
                    self.data_q.put((data, time.time() - t_start))
                    self.run_q.task_done()
                    curr_operation = None
                    
            elif curr_operation == UPDATE:
                
                if wait_T:
                    self.sc.wait_timer_update(wait_T)
                if partition:
                    self.sc.buffer_update(partition[0], partition[1], partition[2])
                if chirp:
                    self.sc.chirp_update(chirp)
                
                self.sc.exit_update()
                self.run_q.task_done()
                curr_operation = None
                
# TODO: determine if data needs to be pruned
class data_writer(Thread):
    def __init__(self, write_queue, dc, exit_cond):
        Thread.__init__(self)
        self.q = write_queue
        self.dc = dc
        self.exit_cond = exit_cond
        
    def run(self):
        while True:
            
            # if we get an exit flag, serve rest of queue and quit
            if self.exit_cond() and self.q.empty():
                break
    
            if not self.q.empty():
                
                data, data_suffix, save_path = self.q.get()
                    
                dc.dump_as_npy(save_path, data, suffix=data_suffix)
                self.q.task_done()
                
            else:
                # 10 ms
                time.sleep(0.01)

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
        
    t_write = data_writer(write_queue, dc, (lambda : write_exit))    
    t_sonar = sonar_run(run_queue, data_queue, sc, (lambda : sonar_exit))    
    
    save_path = dc.create_run_dir()
    nidx = 1
    
    t_write.start()
    t_sonar.start()
    
    t_start = time.time()
        
    while nidx < nruns + 1:
        
        if not data_queue.empty():
            data, t = data_queue.get()
            write_queue.put((data, t, save_path))
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
    
        
    
