#
# Author: Ben Westcott
# Date Created: 1/13/23
#

import numpy as np
import serial
import serial.tools.list_ports
import time
import numpy as np
import time
import selectors

from queue import Queue

import array

from bb_utils import hword_to_bytes
from bb_utils import list2bytearr
from ser_utils import *

EMITTER_PORT = '/dev/cu.usbmodem14301'

def sread(reader, mask, rqueue):
    msg = reader.read(RAW_BUF_LEN)
    frame_type, decoded = decode_msg(bytearray(msg))
    print(f"{frame_type}: {array.array('H', decoded)}")
    time.sleep(1)    

if __name__ == '__main__':
    
    sonar_recorder = serial.Serial('/dev/cu.usbmodem14301', USART_BAUD)
    sel = selectors.DefaultSelector()

    sel.register(sonar_recorder, selectors.EVENT_READ, sread)
    keys= sel.get_map()
    for item in keys.items():
        print(item)

    #while True:
    #    events = sel.select()
    #    for key, mask in events:
    #        callback = key.data
    #        callback(sonar_recorder, mask)

    #sonar_emitter = serial.Serial('/dev/cu.usbmodem14301', USART_BAUD)

    #nchunks = 40
    #dlen = 30000
    lst = np.ones(256, np.uint16) * 4096
    #print(list2bytearr(lst, 2))
    #out_lst = [TX_DATA_FRAME]
    #for n in range(0, 128):
    #    out_lst.extend([0x00, 0x10])

    #out = encode_msg(out_lst)
    #print(out)

    #msg = bytearray(encode_msg(TEST_EMIT_UPD_MSG))
    #print(len(msg))
    #sonar_emitter.write(msg)

    #time.sleep(0.001)
    #for n in range(0, 24):
    #    sonar_emitter.write(bytearray(out))
       # sonar_emitter.flush()

