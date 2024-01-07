#
# Author: Ben Westcott
# Date Created: 12/26/23
#

import numpy as np
import serial
import serial.tools.list_ports
import time
import numpy as np
import time

from scipy import signal
from datetime import datetime
from bb_utils import bin2dec
from bb_utils import list2bytearr

from threading import Thread
from queue import Queue

import bb_log
import m4
import yaml

from hw_defs import *

# Generates a chirp with:
# f0: starting frequency
# f1: ending frequency
# T: time of sweep
# N: number of samples
# Ts: sampling period
# T and N are related by Ts, but all three are passed since
# it is likely that all three are already available and thus
# we do not have to do the arithmatic to find the third value
def generate_chirp(f0, f1, T, N, Ts, method='linear', window='hann'):

    # chirp time vector -- range of time that the chirp takes to sweep
    tv_chirp = np.arange(0, T - Ts, Ts)
    
    # chirp vector
    chirp = signal.chirp(tv_chirp, f0, T, f1, method=method)
    
    win = 1
    if window is not None:
        # TODO: Fix inconsitencies with chirp length and window length
        win = signal.windows.get_window(window, int(N)-1, False)
    
    # DAC outputs 0 to 3.3V, and maps 0-3.3V -> 0-DAC_MAX_INT
    # so, bias 0 to DAC_MAX_INT/2 in order to use DAC full range
    chirp_biased = (np.rint((DAC_MAX_INT/2) * (1 + win*chirp))).astype(int).tolist()
    
    return (tv_chirp, win, chirp_biased)

# tuple containing the default partition. This is the partition that the MCU applies on RESET
part_default = (False, DEFAULT_N, DEFAULT_N_LISTEN, DEFAULT_CHIRP_LEN, DEFAULT_LISTEN_LEN, DEFAULT_LISTEN_LEN)

def check_partition(clen, rlen, llen):

    # negatives not allowed
    clen = np.absolute(clen)
    rlen = np.absolute(rlen)
    llen = np.absolute(llen)

    # Get number of listen samples, and total number of samples
    N_listen = rlen + llen
    N = N_listen + clen
    
    # sum doesnt exceed the maximum buffer length for data acquisition
    # we are limited by RAM space here
    if N > MAX_BUFFER_LENGTH:
        return part_default
    
    # A single descriptor can only carry at most max(uint16_t), so check for that.
    # This can be extended so that MAX_DESCRIPTOR_LENGTH = MAX_BUFFER_LENGTH if
    # we use linked descriptors
    if clen > MAX_DESCRIPTOR_LENGTH or rlen > MAX_DESCRIPTOR_LENGTH or llen > MAX_DESCRIPTOR_LENGTH:
        return part_default
    
    return (True, N, N_listen, clen, rlen, llen)

# MCU sends listen data in chunks of 64 bytes, so
# if 64 doesnt divide the length, then add an
# additional chunk. When data is received,
# prune it to length
def determine_chunk_count(length):
    blen = 2*length              # length in bytes
    if blen <= S_CHUNK_LENGTH:
        return 1
    cnt = int(blen/S_CHUNK_LENGTH)
    if blen % S_CHUNK_LENGTH:
        cnt = cnt + 1
    return cnt

# Max freq: TCC1_GCLK_FREQ/(1024 * TCC_MAX_TOP) = 120MHz/(1024 * 65535) = 1.788 Hz
# Max period = 1/1.788 = 0.559 sec
T_wait_max = 0.559
# Min freq: TCC1_GCLK_FREQ/(1 * TCC_MIN_TOP) = 120MHz/(1 * 50) = 2.400 MHz
# Min period = 1/1.2E6 = 0.4167 usec
T_wait_min = 0.4167E-6

# Takes a desired period of time as an input, and determines 
# an appropriate prescaler and counter value which will produce
# that period (within a margin of error)
def determine_timer_vals(T_out):
    # if input is greater than the maximum period, return maximum period
    if T_out >= T_wait_max:
        return (T_wait_max, TCC_MAX_TOP, TCC_PRESCALER_DIV1024, 1024)
    
    # if input is less than minimum period, return minimum period
    if T_out <= T_wait_min:
        return (T_wait_min, TCC_MIN_TOP, TCC_PRESCALER_DIV1, 1)
    
    # ratio of undivided timer clock and desired period
    # is factored out since it is constant
    ratio = TCC1_GCLK_FREQ * T_out

    for i in range(0, len(PRESCALERS)):
        TOP = (ratio / PRESCALERS[i]) - 1
        if TOP <= TCC_MAX_TOP:
            return (T_out, int(TOP), PRESCALER_REG_VALS[i], PRESCALERS[i])
            
    return (None, None, None, None)
    
class SonarThread(Thread):
    def __init__(self, run_queue, data_queue, Sonar, exit_cond):
        Thread.__init__(self)
        self.run_q = run_queue
        self.data_q = data_queue
        self.Sonar = Sonar
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
                    self.Sonar.enter_update()
                else:
                    curr_operation = RUN
                    self.Sonar.start_job(do_chirp=do_chirp)
                    t_start = time.time()
                    
            if curr_operation == RUN:
                if data := self.Sonar.get_job() is not None:
                    self.data_q.put((data, time.time()  - t_start))
                    self.run_q.task_done()
                    curr_operation = None
                    
            elif curr_operation == UPDATE:
                
                if wait_T:
                    self.Sonar.wait_timer_update(wait_T)
                if partition:
                    self.Sonar.buffer_update(partition[0], partition[1], partition[2])
                if chirp:
                    self.Sonar.chirp_update(chirp)
                    
                self.Sonar.exit_update()
                self.run_q.task_done()
                curr_operation = None
        
class SonarController:

    def __init__(self, m4, bat_log):
    
        self.bat_log = bat_log
        self.m4 = m4
        
        # sampling rate and period
        self.Fs = SAMPLING_RATE
        self.Ts = 1/SAMPLING_RATE
        
        # indicates whether MCU is in update condition or not
        self.updating = False
        # indicates whether a job is in process
        self.running = False
            
        self.load_defaults()
        self.bat_log.info("[Sonar] controller ready")
        
    def load_defaults(self):
        self.enter_update()
        self.buffer_update(DEFAULT_CHIRP_LEN, DEFAULT_LISTEN_LEN, DEFAULT_LISTEN_LEN)
        
        self.T_wait, self.TOP_wait, self.Preg_wait, self.P_wait = determine_timer_vals(DEFAULT_T_WAIT)
        self.wait_timer_update(DEFAULT_T_WAIT)
        
        default_chirp = (DAC_MAX_INT/2)*(np.ones(DEFAULT_CHIRP_LEN))
        with open('default_chirp.npy', 'rb') as fp:
            default_chirp = np.load(fp)
        
        self.chirp_update(list(default_chirp))
        self.exit_update()
            
        self.refresh_listen_times()
        self.bat_log.info("[Sonar] Loaded defaults.")
        
    # update time periods depending on num samples / timer vals
    def refresh_listen_times(self):
        self.T_chirp = self.N_chirp/self.Fs
        self.T_listenR = self.N_listenR/self.Fs
        self.T_listenL = self.N_listenL/self.Fs
        self.T_listen = self.T_listenR + self.T_listenL
        self.T = self.T_listen + self.T_chirp
    
    # enter_update must be called before any update_* functions
    def enter_update(self):
        if self.updating:
            return False
            
        self.m4.write([SOP_COMMAND, OP_UPDATE_JOB])
        self.updating = True
        return True

    # b_array can be supplied if computed beforehand. Otherwise we have
    # check for validity and convert lengths into a byte array
    def buffer_update(self, clen, rlen, llen, b_array=None):
    
        if not self.updating:
            return False
        
        self.m4.write([SOP_COMMAND, UOP_BUFFER])

        if b_array is None:
            # check to ensure that we are sending a valid partition
            _, N, N_listen, clen, rlen, llen = check_partition(clen, rlen, llen)
            b_array = list2bytearr([clen, rlen, llen], 2)

        self.m4.write(b_array)
        
        # update sample lengths to reflect the changes
        # made on the MCU
        self.N_chirp = clen
        self.N_listenR = rlen
        self.N_listenL = llen
        self.N_listen = rlen + llen
        self.N = self.N_listen + clen
        self.N_chunks = determine_chunk_count(self.N_listen)
                
        return True
            
    # enforce the length of the buffer before calling
    # I didnt want to deal with padding if length < N_chirp
    # because zero padding would produce harmonics and
    # exp(-x) padding seems too not worth it
    # TODO: Honestly, it should be up to the user to ensure 
    # the chirp buffer contains data that wont produce
    # harmonics. But, we maybe still can generate warnings
    # when, for example, the buffer contains integers that 
    # the DAC is unable to output (0 - 4096) or if the buffer is
    # zero padded.
    def chirp_update(self, buffer, b_array=None):
        
        if not self.updating:
            return False
        
        if len(buffer) != self.N_chirp:
            return False
            
        self.m4.write([SOP_COMMAND, UOP_CHIRP])
        
        if b_array is None:
            b_array = list2bytearr(buffer, 2)
        
        self.m4.write([SOP_DATA])
        self.m4.write(b_array)
        return True
        
    def wait_timer_update(self, period):
        
        if not self.updating:
            return False
        
        T, TOP, reg_val, P = determine_timer_vals(period)
        #print(f"{T},{TOP},{reg_val},{P}\n")
        if TOP != self.TOP_wait:
            self.m4.write([SOP_COMMAND, UOP_WAIT_TIMER_TOP])
            b = list2bytearr([TOP], 2)
            #print(f"TOP: {b}\n")
            self.m4.write(list2bytearr([TOP], 2))
            self.TOP_wait = TOP
            
        if reg_val != self.Preg_wait:
            #print(f"reg: {[SOP_COMMAND, UOP_WAIT_TIMER_PRESCALER, reg_val]}")
            self.m4.write([SOP_COMMAND, UOP_WAIT_TIMER_PRESCALER, reg_val])
            self.Preg_wait = reg_val
            self.P_wait = P
        
        self.T_wait = T
        return True
    
    # Needs to be called when finished updating
    def exit_update(self):
        
        # We cannot exit an update if we
        # never entered one
        if not self.updating:
            return False
            
        self.m4.write([SOP_COMMAND, UOP_FINISH])
        
        # MCU responds to exit update indicating it was
        # successful, but this isnt really needed
        self.m4.read(1)
        
        # We can now start jobs
        self.updating = False
        return True
        
    # Even if we have space partitioned for the chirp,
    # we do not always want to chirp, so we can send the 
    # run opcode with a boolean indicating whether to chirp or not
    def start_job(self, do_chirp=True):
        
        # Cant start job if MCU is still in update state
        # or if it is currently processing a job
        if self.updating or self.running:
            return False
        
        self.running = True    
        self.m4.write([SOP_COMMAND, OP_START_JOB, do_chirp])
        return True
     
    # get_job will return:
    #
    # False:
    #  if MCU is in update state
    #  if a job wasnt started, or if N_listen = 0, i.e. we do not expect data back
    #
    # None: if we are still waiting for the job to complete
    #
    # Data: if run is completed
    def get_job(self):
        
        if self.updating or not self.running:
            return False    
        
        if self.m4.in_waiting() <= 0:
            return None
            
        data = self.m4.read(S_CHUNK_LENGTH * self.N_chunks)
        
        self.running = False
        return data
        
    def amp_enable(self):
        self.m4.write([SOP_COMMAND, OP_AMP_ENABLE])
    
    def amp_disable(self):
        self.m4.write([SOP_COMMAND, OP_AMP_DISABLE])
        
    def is_updating(self):
        return self.updating
        
    def is_running(self):
        return self.running
        
    def get_num_listen_samples(self):
        return self.N_listen
        
