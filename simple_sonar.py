#
# Author: Ben Westcott
# Date Created: 1/24/23
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
from bb_utils import search_comports

from ser_utils import *
from emit import build_emit_upd
from emit import validate_emit_upd

from hw_defs import ADC_SAMPLING_RATE

EMITTER_SERIAL_NO = '6A3E92CE5351523450202020FF0E4431'
RECORDER_SERIAL_NO = 'E9139F095351523450202020FF0E3632'

RECORD_TIME = 25E-3
TIME_PER_CHUNK = 64/ADC_SAMPLING_RATE

N_RECV_CHUNKS = int(RECORD_TIME//TIME_PER_CHUNK + 1)

def read_fun(reader, mask):
    msg = reader.read(RAW_BUF_LEN)
    frame_type, decoded = decode_msg(bytearray(msg))
    return frame_type, decoded

if __name__ == '__main__':

    emitter = search_comports([EMITTER_SERIAL_NO])
    e_stream = serial.Serial(emitter.device, baudrate=USART_BAUD)

    chirp = None
    with open('default_chirp.npy', 'rb') as fd:
        chirp = np.load(fd)

    chunks, _ = build_emit_upd(len(chirp), chirp.astype(np.uint16))

    for chunk in chunks:
        e_stream.write(chunk)
        e_stream.flush()

    nrecv = 0

    recorder = search_comports([RECORDER_SERIAL_NO])
    r_stream = serial.Serial(recorder.device, baudrate=USART_BAUD)

    #sel = selectors.DefaultSelector()
    #sel.register(r_stream, selectors.EVENT_READ, read_fun)

    data = bytearray()
    while nrecv < N_RECV_CHUNKS:
        msg = r_stream.read(RAW_BUF_LEN)
        frame_type, decoded = decode_msg(bytearray(msg))
        #print(f"{nrecv}: {frame_type}: {array.array('H', decoded)}")
        nrecv += 1

        
        
    print(len(data))



