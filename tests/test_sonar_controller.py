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
        sonar_book = conf['sonar']
        
        sonar_m4 = m4.M4(conf['sonar_boards'], conf['sonar_baud'], bat_log)
        sonar = SonarController(sonar_book, sonar_m4, bat_log)
        
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
            
        tester.assertEqual(len(data), 2*(rlen + llen))
        tester.assertFalse(sonar.is_running())
        #print(f"{n}, ")
        
class TestSonarController(unittest.TestCase):
    
    def setUp(self):
        bat_log = bb_log.get_log()
        self.sonar = init_board(bat_log)
    
    def test_basic_buffer_upd(self):
        clen = 3000
        rlen = 30000
        llen = 30000
        
        self.assertTrue(self.sonar.enter_update())
        self.assertTrue(self.sonar.is_updating())
        self.assertFalse(self.sonar.is_running())
        
        self.assertTrue(self.sonar.buffer_update(clen, rlen, llen))
        
        self.assertTrue(self.sonar.exit_update())
        self.assertFalse(self.sonar.is_updating())
        
        self.assertTrue(self.sonar.start_job())
        self.assertTrue(self.sonar.is_running())
        self.assertFalse(self.sonar.is_updating())
        
        data = self.sonar.get_job()
        while data is None:
            data = self.sonar.get_job()
            
        self.assertEqual(len(data), 2*(rlen + llen))
        self.assertFalse(self.sonar.is_running())
        
        do_n_runs(self, self.sonar, 10, rlen, llen)
        
if __name__ == '__main__':
    #unittest.main()
    
    bat_log = bb_log.get_log()
    sonar = init_board(bat_log)
    
    # Trying to see how long it takes to send one 
    # sample. 1 sample ideally takes 1us + a little more
    # to arrive in the data buffer, so negligable for now.
    sonar.enter_update()
    sonar.buffer_update(3000, 1, 0)
    sonar.exit_update()
    
    s = 0
    for n in range(0, 10):
        t = time_single_run(sonar)
        s += t   
        
    
    # Exit timers are set to: (65535 * 1)/120MHz = 0.55 ms
    # Wait timer is set to: (100 * 4)/120MHz = negligable
    # So, total intentional latency = 0.55 ms
    # I got about 0.73 ms for one sample, so 0.18 ms are spent
    # to get the sample (which is two bytes i.e. a uint16_t)! 
    # TODO: Create an SPI lane to send the data, or figure out why
    # UART is so slow.
    print(f"{s}, {s/10}")   
        