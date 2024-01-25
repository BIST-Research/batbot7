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

def sread(reader, mask, idx):
    msg = reader.read(RAW_BUF_LEN)
    frame_type, decoded = decode_msg(bytearray(msg))
    print(f"{idx: } {frame_type}: {array.array('H', decoded)}")
# 128 uint16 --> 0.128 ms
if __name__ == '__main__':
    
    #sonar_emitter = serial.Serial('/dev/cu.usbmodem14301', USART_BAUD)

    #chirp = None
    #with open('default_chirp.npy', 'rb') as fd:
    #    chirp = np.load(fd)

    #chunks, _ = build_emit_upd(len(chirp), chirp.astype(np.uint16))

    #for chunk in chunks:
    #    sonar_emitter.write(chunk)
        #sonar_emitter.flush()

    sonar_recorder = serial.Serial('/dev/cu.usbmodem14401', USART_BAUD)
    sel = selectors.DefaultSelector()

    sel.register(sonar_recorder, selectors.EVENT_READ, sread)
    keys= sel.get_map()
    #for item in keys.items():
    #    print(item)
    idx = 0
    while True:
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(sonar_recorder, mask, idx)
            idx += 1


