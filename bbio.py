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
from bb_utils import bin2dec
from ser_utils import *
from emit import build_emit_upd
from emit import validate_emit_upd


EMITTER_PORT = '/dev/cu.usbmodem14301'

def sread(reader, mask, rqueue):
    msg = reader.read(RAW_BUF_LEN)
    frame_type, decoded = decode_msg(bytearray(msg))
    print(f"{frame_type}: {array.array('H', decoded)}")
    time.sleep(1)    

if __name__ == '__main__':
    
    #sonar_recorder = serial.Serial('/dev/cu.usbmodem14301', USART_BAUD)
    #sel = selectors.DefaultSelector()

    #sel.register(sonar_recorder, selectors.EVENT_READ, sread)
    #keys= sel.get_map()
    #for item in keys.items():
    #    print(item)

    #while True:
    #    events = sel.select()
    #    for key, mask in events:
    #        callback = key.data
    #        callback(sonar_recorder, mask)

    sonar_emitter = serial.Serial('/dev/cu.usbmodem14301', USART_BAUD)

    chirp = None
    with open('default_chirp.npy', 'rb') as fd:
        chirp = np.load(fd)

    #validate_emit_upd(4, chirp, len(chirp))
    

    #start_time = 0
    #end_time = 3E-3
    #sample_rate = 1000000
    #time = np.arange(start_time, end_time, 1/sample_rate)
    #frequency = 1E3
    #s = (4095/2) * (1 + np.sin(2* np.pi*frequency*time))

    chunks, _ = build_emit_upd(len(chirp), chirp.astype(np.uint16))

    #print(len(msgs))

    for chunk in chunks:
    ##    #print(chunk)
        sonar_emitter.write(chunk)
        sonar_emitter.flush()
    #print(chunks)
    #nchunks = 40
    #dlen = 30000

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

