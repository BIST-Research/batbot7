import numpy as np
import time
import os
import numpy as np
from scipy import signal
from datetime import datetime
import bb_log
import m4
import yaml

from bb_utils import get_timestamp_now

class DataController:
    
    def __init__(self, conf_name, bat_log):
        
        self.bat_log = bat_log
        conf = None
        with open(conf_name) as fd:
        
            conf = yaml.safe_load(fd)
            fd.close()
            
        if conf is None:
            self.bat_log.critical(f"Please check if your configuration file exists and is parseable!")
            exit()
            
        self.bat_log.debug(f"Found {conf_name}, loading settings...")
        
        self.sonar_boards = list(conf['sonar_boards'])
        self.sonar_baud = int(conf['sonar_baud'])
        self.do_plot = bool(conf['do_plot'])
        
        self.sonar_book = conf['sonar']
        self.sonar_plot_book = conf['sonar_plot']
        self.gps_book = conf['gps']
        
        parent_directory = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = parent_directory + f"/{str(conf['data_directory'])}"
        
        if not os.path.exists(self.data_dir):
            bat_log.debug(f"Creating root data path... ")
            os.makedirs(self.data_dir)
            
    def create_run_dir(self, suffix=None):
        run_dir = f"{get_timestamp_now()}"
        if suffix is not None:
            run_dir += f"_{str(suffix)}"
        
        os.makedirs(self.data_dir + "/" + run_dir)
        return run_dir
        
    def dump_as_npy(self, dir_name, data, suffix=None):
    
        path = f"{self.data_dir}/{dir_name}/{get_timestamp_now()}"
        if suffix is not None:
            path += f"_{str(suffix)}"
        
        path += ".npy"
        
        with open(path, 'wb') as fd:
            np.save(fd, np.array(data))
            fd.close()
            
    def get_sonar_boards(self):
        return self.sonar_boards
        
    def get_sonar_baud(self):
        return self.sonar_baud
        
    def get_sonar_book(self):
        return self.sonar_book
        
    def get_sonar_plot_book(self):
        return self.sonar_plot_book
        
    def get_gps_book(self):
        return self.gps_book
        
        
if __name__ == '__main__':
    
    conf_name = 'bat_conf.yaml'
    bat_log = bb_log.get_log()
    
    data_controller = DataController(conf_name, bat_log)
    dir1 = data_controller.create_run_dir()
    
    dump_list = []
    for x in range(0, 10000):
        dump_list.append(0xf3)
        
    data_controller.dump_as_npy(dir1, dump_list)
    
    dir2 = data_controller.create_run_dir(suffix="test")
    
    data_controller.dump_as_npy(dir2, dump_list, suffix="test")

    
    
            
        
        
        
            
        
            
    
    
        
                


        
        
        
        
            
            
        
