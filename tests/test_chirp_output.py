#
# Author: Ben Westcott
# Date Created: 1/6/23
#

# used to verify chirp output

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

if __name__ == '__main__':
    
    bat_log = bb_log.get_log()
    dc = DataController('test_bat_conf.yaml', bat_log)
    
    sonar_m4 = m4.M4(dc.get_sonar_boards(), dc.get_sonar_baud(), bat_log)
    sc = SonarController(sonar_m4, bat_log)
    
    save_path = dc.create_run_dir()
    
    nruns = 50
    nidx = 0
    
    sc.enter_update()
    sc.wait_timer_update(0.4)
    sc.exit_update()
    
    while nidx < nruns:
        
        sc.start_job()
        
        data = sc.get_job()
        if data is not None and data is not False:
            print("done")
            nidx += 1
            
                    
        
    
    
