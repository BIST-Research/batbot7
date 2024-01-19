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

import array

from ser_utils import decode_msg
from ser_utils import encode_msg

USART_BAUD = 115200

DATA_LEN = 256
SER_BUF_LEN = 2*DATA_LEN + 3

TX_ERR = 0x40
TX_NONE = 0x41
TX_MSG_FRAME = 0x42
TX_DATA_FRAME = 0x43

TEST_EMIT_UPD_MSG = [TX_MSG_FRAME, 0x01, 0x0b, 0xb8, 0x00, 0x18]

def sread(reader, mask):
    msg = reader.read(2*DATA_LEN + 3)
    frame_type, decoded = decode_msg(bytearray(msg))
    print(f"{frame_type}: {array.array('H', decoded)}")
    time.sleep(1)
    
if __name__ == '__main__':
    
    #sonar_recorder = serial.Serial('/dev/cu.usbmodem14301', USART_BAUD)
    
    #sel = selectors.DefaultSelector()

    #sel.register(sonar_recorder, selectors.EVENT_READ, sread)

    #while True:
    #    events = sel.select()
    #    for key, mask in events:
    #        callback = key.data
    #        callback(sonar_recorder, mask)

    sonar_emitter = serial.Serial('/dev/cu.usbmodem14301', USART_BAUD)

    nchunks = 40
    dlen = 30000

    out_lst = [TX_DATA_FRAME]
    for n in range(0, 128):
        out_lst.extend([0x00, 0x10])

    out = encode_msg(out_lst)
    print(out)

    msg = bytearray(encode_msg(TEST_EMIT_UPD_MSG))
    print(len(msg))
    sonar_emitter.write(msg)

    #time.sleep(0.001)
    for n in range(0, 24):
        sonar_emitter.write(bytearray(out))
       # sonar_emitter.flush()
