#
# Author: Ben Westcott
# Date Created: 12/30/23
#

import os, sys
sys.path.append("../")

import numpy as np
import time
import unittest

import bb_log
import m4
import yaml

from bb_sonar import determine_timer_vals
from bb_sonar import generate_chirp
from bb_sonar import check_partition
from bb_sonar import determine_chunk_count
from bb_sonar import SonarController
from bb_sonar import part_default

from hw_defs import *

def init_board(bat_log):
    sonar = None
    with open('test_bat_conf.yaml') as fd:
        conf = yaml.safe_load(fd)
        
        sonar_m4 = m4.M4(conf['sonar_boards'], conf['sonar_baud'], bat_log)
        sonar = SonarController(sonar_m4, bat_log)
        
        fd.close()
    return sonar
    
def time_single_run(sonar):
    sonar.start_job()
    start = time.time()
    
    #sonar.m4.read(1)
    data = sonar.get_job()
    while data is None:
        data = sonar.get_job()
            
    return time.time() - start
    
def do_n_runs(tester, sonar, N, rlen, llen):
    
    for n in range(0, N):
        tester.assertTrue(sonar.start_job())
        tester.assertTrue(sonar.is_running())
        tester.assertFalse(sonar.is_updating())
        
        data = sonar.get_job()
        while data is None:
            data = sonar.get_job()
            
        tester.assertEqual(len(data), sonar.N_chunks * S_CHUNK_LENGTH)
        tester.assertFalse(sonar.is_running())
        #print(f"{n}, ")
   
class TestSonarController(unittest.TestCase):
    
    def setUp(self):
        bat_log = bb_log.get_log()
        self.sonar = init_board(bat_log)
        self.clen = 3000
        self.rlen = 30000
        self.llen = 30000
        
    def assert_enter_update(self):
        self.assertTrue(self.sonar.enter_update())
        self.assertTrue(self.sonar.is_updating())
        self.assertFalse(self.sonar.is_running())
        
    def assert_exit_update(self):
        self.assertTrue(self.sonar.exit_update())
        self.assertFalse(self.sonar.is_updating())
        
    def assert_start_job(self):
        self.assertTrue(self.sonar.start_job(do_chirp=True))
        self.assertTrue(self.sonar.is_running())
        self.assertFalse(self.sonar.is_updating())
        
    def assert_n_runs(self, N, print_time=False):
                    
        for n in range(0, N):
            self.assert_start_job()
            
            start_time = time.time()
            
            data = self.sonar.get_job()       
            while data is None:
                data = self.sonar.get_job()
            
            end_time = time.time()
            
            if print_time:
                print(f"{n}: {end_time - start_time}")
                
            self.assertEqual(len(data), self.sonar.N_chunks * S_CHUNK_LENGTH)                
            self.assertFalse(self.sonar.is_running())
        
    def test_basic_buffer_upd(self):

        
        self.assert_enter_update()
        
        self.assertTrue(self.sonar.buffer_update(self.clen, self.rlen, self.llen))
        
        self.assert_exit_update()
        
        self.assert_start_job()
        
        data = self.sonar.get_job()
        while data is None:
            data = self.sonar.get_job()
            
        self.assertEqual(len(data), 2*(self.rlen + self.llen))
        self.assertFalse(self.sonar.is_running())
        
        self.assert_n_runs(10, print_time=True)
        #do_n_runs(self, self.sonar, 10, self.rlen, self.llen)
        
    def test_wait_timer_upd_buffer_upd_chirp_upd(self):
        
        it = 30
        
        self.sonar.amp_enable()
        
        #tv = np.linspace(0.5E-6, 0.5, it)
        # TODO: the case where listenL = listenR = 0 doesnt work. 
        # The update condition is either not reached on the subsequent update condition,
        # or we get stuck in update condition.
        tv = [0.5, 1E-6, 5E-5, 6E-5, 8E-4, 9E-6, 3E-2, 4E-2, 9E-4, 0.5E-6]
        cv = np.linspace(10, it * 100, it)
        lv = np.linspace(10, it * 1000, it)
        rv = np.linspace(10, it * 1000, it)
        
        nv = np.linspace(it, 1, it)
        
        picker = 1
        for t,c,l,r,n in zip(tv, cv, lv, rv, nv):
            
            ci, li, ri, ni = (int(c), int(l), int(r), int(n))
            
            x_wave = np.linspace(0, ci, ci)
            wave = (DAC_MAX_INT/2) * (1 + np.sin(x_wave))
            wave_out = [int(w) for w in wave]
            
            self.assert_enter_update()
            
            if picker % 7 == 0:
                self.assertTrue(self.sonar.wait_timer_update(t))
                self.assertTrue(self.sonar.buffer_update(ci, li, ri))
                self.assertTrue(self.sonar.chirp_update(wave_out))
            elif picker % 5 == 0:
                self.assertTrue(self.sonar.buffer_update(ci, li, ri))
                self.assertTrue(self.sonar.chirp_update(wave_out))
                self.assertTrue(self.sonar.wait_timer_update(t))
            elif picker % 3 == 0:
                self.assertTrue(self.sonar.wait_timer_update(t))
            else:
                self.assertTrue(self.sonar.buffer_update(ci, li, ri))
                
                
            #self.assertTrue(self.sonar.wait_timer_update(tr))
            #self.assertTrue(self.sonar.buffer_update(ci, ri, li))
            self.assert_exit_update()
            
            print(f"clen={ci}\trlen={ri}\tllen={li}\tnruns={ni}\twait={t}")
            self.assert_n_runs(ni, print_time=True)
                        
            picker += 1 
            
        self.sonar.amp_disable()
                 
            
    def test_single_chirp_upd(self):
        
        x_wave = np.linspace(0, 3000, 3000)
        wave = (DAC_MAX_INT/2) * (1 + np.sin(x_wave))
        wave_out = [int(w) for w in wave]
        period = 1E-6
        
        self.assert_enter_update()
        self.assertTrue(self.sonar.wait_timer_update(period))
        self.assertTrue(self.sonar.buffer_update(3000, 10000, 10000))
        self.assertTrue(self.sonar.chirp_update(wave_out))
        self.assert_exit_update()
        self.assert_n_runs(10, print_time = True)
        
        #self.assert_enter_update()
        #self.assert_exit_update()
        
        #do_n_runs(self, self.sonar, 1, 10000, 10000)
        
if __name__ == '__main__':
    unittest.main()
    
    #bat_log = bb_log.get_log()
    #sonar = init_board(bat_log)
    
    #x_wave = np.linspace(0, 3000, 3000)
    #wave = np.sin(x_wave)
    
    #wave = (DAC_MAX_INT/2) * (1 + np.sin(x_wave))
    #wave_out = [int(w) for w in wave]
    #period = 1E-6
    
    # Trying to see how long it takes to send one 
    # sample. 1 sample ideally takes 1us + a little more
    # to arrive in the data buffer, so negligable for now.
    #sonar.enter_update()
    #sonar.buffer_update(3000, 1000, 1000)
    #sonar.chirp_update(wave_out)
    #sonar.wait_timer_update(6E-4)
    #sonar.exit_update()
    
    #t = time_single_run(sonar)
    #t = time_single_run(sonar)
    #t = time_single_run(sonar)
    #print(t)
    #time_single_run(sonar)
        
    
    #s = 0
    #for n in range(0, 10):
    #    t = time_single_run(sonar)
    #    s += t   
        
    
    # Exit timers are set to: (65535 * 1)/120MHz = 0.55 ms
    # Wait timer is set to: (100 * 4)/120MHz = negligable
    # So, total intentional latency = 0.55 ms
    # I got about 0.73 ms for one sample, so 0.18 ms are spent
    # to get the sample (which is two bytes i.e. a uint16_t)! 
    # TODO: Create an SPI lane to send the data, or figure out why
    # UART is so slow.
    #print(f"{s}, {s/10}") 