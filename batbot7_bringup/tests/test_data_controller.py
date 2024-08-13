#
# Author: Ben Westcott
# Date Created: 1/5/23
#

import os, sys
sys.path.append("../")

from bb_data import DataController
import bb_log

if __name__ == '__main__':
    
    bat_log = bb_log.get_log()
    
    dc = DataController('test_bat_conf.yaml', bat_log)
    
    assert os.path.exists(dc.get_data_directory())
    
    sonar_boards = dc.get_sonar_boards()
    
    assert type(sonar_boards) == list
    
    sonar_baud = dc.get_sonar_baud()
    
    assert type(sonar_baud) == int
    
    sonar_plot_book = dc.get_sonar_plot_book()
    
    assert type(sonar_plot_book['spec_color_map']) == str
    assert type(sonar_plot_book['update_interval']) == int
    assert type(sonar_plot_book['calibration_interval']) == int
    assert type(sonar_plot_book['y_amplitude_padding']) == int
    
    fft_book = sonar_plot_book['fft_settings']
    
    assert type(fft_book['NFFT']) == int
    assert type(fft_book['noverlap']) == int
    
    gps_book = dc.get_gps_book()
    
    assert type(gps_book['do_gps']) == bool
    assert type(gps_book['ser_port']) == str
    assert type(gps_book['baud_rate']) == int
    assert type(gps_book['timeout']) == int
    assert type(gps_book['do_rtk_correction']) == bool
    
    ntrip_book = gps_book['ntrip']
    
    assert type(ntrip_book['ipprot']) == str
    assert type(ntrip_book['server']) == str
    assert type(ntrip_book['port']) == int
    assert type(ntrip_book['flowinfo']) == int
    assert type(ntrip_book['scopeid']) == int
    assert type(ntrip_book['mountpoint']) == str
    assert type(ntrip_book['username']) == str
    assert type(ntrip_book['password']) == str
    assert type(ntrip_book['ggamode']) == int
    assert type(ntrip_book['ggaint']) == int
    assert type(ntrip_book['reflat']) == float
    assert type(ntrip_book['reflon']) == float
    assert type(ntrip_book['refalt']) == float
    assert type(ntrip_book['refsep']) == float
    
    
    
    
    
    
