#
# Author: Ben Westcott
# Date Created: 12/28/23
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

class TestSonarStaticMethods(unittest.TestCase):
    
    def test_determine_chunk_count(self):
        # S_CHUNK_LENGTH = 64 does not divide 2*30000
        # so we should get floor(60000/64) + 1
        self.assertEqual(determine_chunk_count(30000), 938)
        # 64 does divide 2*60000
        # so we should get floor(120000/64)
        self.assertEqual(determine_chunk_count(60000), 1875)
        
    def test_check_partition(self):
        # Check valid cases first
        #clen = 3000
        #rlen = 10000
        #llen = 10000
        t = (3000, 10000, 10000)
        target = (True, 23000, 20000, 3000, 10000, 10000)
        self.assertEqual(check_partition(t[0], t[1], t[2]), target)
        
        # part default is returned on any invalid partition
        target = part_default
        
        # test for sum > MAX_LENGTH
        t = (40000, 40000, 40000)
        self.assertEqual(check_partition(t[0], t[1], t[2]), target)
        
        # test for MAX_DESCRIPTOR_LENGTH
        t = (70000, 0, 0)
        self.assertEqual(check_partition(t[0], t[1], t[2]), target)
        t = (0, 70000, 0)
        self.assertEqual(check_partition(t[0], t[1], t[2]), target)
        t = (0, 0, 70000)
        self.assertEqual(check_partition(t[0], t[1], t[2]), target)

    def test_determine_timer_vals(self):
        
        # check valid range first
        tv = np.linspace(0.5E-6, 0.5, 300)
        
        decimal = 7
        
        for t in tv:
            T, TOP, Preg, P = determine_timer_vals(t)
            self.assertAlmostEqual((TOP * P)/TCC1_GCLK_FREQ, t, 2)
            
    def test_generate_chirp(self):
            pass
            

            

def basic_sonar_test():
    bat_log = bb_log.get_log()
    
    with open('test_bat_conf.yaml') as fd:
        conf = yaml.safe_load(fd)
        sonar_book = conf['sonar']
        
        sonar_m4 = m4.M4(conf['sonar_boards'], conf['sonar_baud'], bat_log)
        
        sonar = SonarController(sonar_book, sonar_m4, bat_log)
        
        sonar.enter_update()
        sonar.buffer_update(3000, 30000, 0)
        sonar.exit_update()
        
        sonar.start_job(do_chirp=True)
        
        buf = sonar.get_job()
        while buf is None:
            buf = sonar.get_job()
            
        print(len(buf))
        sonar.enter_update()
        sonar.buffer_update(0, 10000, 30000)
        sonar.exit_update()
        
        sonar.start_job(do_chirp=False)
        
        buf = sonar.get_job()
        while buf is None:
            buf = sonar.get_job()
            
        print(len(buf))
        
        for n in range(0, 20):
            sonar.start_job()
            data = sonar.get_job()
            while data is None:
                data = sonar.get_job()
            print(f"{n}, ")    
            
if __name__ == '__main__':
    
    basic_sonar_test()
    #unittest.main()
    
    #tv = np.linspace(0.5E-6, 0.5, 10)
    #T, TOP, P = determine_timer_vals(0.01)
    #print(f"{T},{TOP},{P}")
    
    #for t in np.linspace(0.5E-6, 0.5, 10):
    #    T, TOP, P = determine_timer_vals(t)
    #    print(f"{T}, {TOP}, {P}\n")
        
        
        
        
        
        
        
    
    
    
    
    
    
