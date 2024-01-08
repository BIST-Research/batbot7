#
# Author: Ben Westcott
# Date Created: 1/5/23
#

# used to test sonar and data controllers

from queue import Queue

RUN_W_CHIRP = (False, True, None, None, None)
RUN_WO_CHIRP = (False, False, None, None, None)

def simple_test():
    ret = Queue(maxsize=100)
    
    ret.put(RUN_W_CHIRP)
    ret.put(RUN_W_CHIRP)
    ret.put((True, False, 0.2E-4, (3000, 10000, 10000), None))
    ret.put(RUN_W_CHIRP)
    ret.put(RUN_W_CHIRP)
    ret.put(RUN_W_CHIRP)
    ret.put(RUN_W_CHIRP)
    ret.put(RUN_W_CHIRP)
    ret.put(RUN_W_CHIRP)
    ret.put((True, False, 2E-6, (3000, 10000, 0), None))
    ret.put(RUN_W_CHIRP)
    ret.put(RUN_W_CHIRP)
    ret.put(RUN_W_CHIRP)
    ret.put(RUN_W_CHIRP)
    ret.put(RUN_W_CHIRP)
    ret.put(RUN_W_CHIRP)
    
    nruns = 14
    status_interval = 1
    
    return ret, nruns, status_interval
    
def long_test_one_mic():
    ret = Queue(maxsize=10000)
    
    ret.put((True, False, 1E-6, (3000, 10000, 0), None))
    
    nruns = 1000
    status_interval = 100
    for n in range(0, nruns):
        ret.put(RUN_W_CHIRP)
    
    return ret, nruns, status_interval
        
def long_test_no_mic():
    ret = Queue(maxsize=10000)
    
    ret.put((True, False, 1E-6, (3000, 10, 0), None))
    
    nruns = 1000
    status_interval = 100
    for n in range(0, nruns):
        ret.put(RUN_W_CHIRP)
    
    return ret, nruns, status_interval
    
def many_partition_test():
    ret = Queue(maxsize=1000)
    
    listen_vec = reversed(range(5000, 10000, 50))
    nruns = 200
    status_interval = 1
    
    for n in listen_vec:
        ret.put((True, False, 1E-6, (3000, n, n), None))
        ret.put(RUN_W_CHIRP)
        ret.put(RUN_WO_CHIRP)
                
    return ret, nruns, status_interval
        
