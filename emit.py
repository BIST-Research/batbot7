#
# Author: Ben Westcott
# Date Created: 1/20/24
#

import numpy as np

from bb_utils import *
from ser_utils import *

from hwdefs import DAC_MAX_INT
from hwdefs import DAC_SAMPLING_RATE

TEST_EMIT_UPD_MSG = [TX_MSG_FRAME, 0x01, 0x0b, 0xb8, 0x00, 0x18]

# 2**15
MAX_EMIT_LENGTH = 32768

EMIT_VALIDATE_LENGTH = 0b00000001
EMIT_VALIDATE_DAC_BOUNDS = 0b00000010
EMIT_VALIDATE_STRENGTH = 0b00000100
    
def validate_emit_upd(mask, data, size):

    ret_val = 0
    if mask & EMIT_VALIDATE_LENGTH and size > MAX_EMIT_LENGTH:
        ret_val |= EMIT_VALIDATE_LENGTH

    if np.max(data) > DAC_MAX_INT or np.min(data) < 0:
        ret_val |= EMIT_VALIDATE_DAC_BOUNDS

    dx = 1E-6
    dydx = np.diff(data)
    [print(n) for n in dydx]


def build_emit_upd(emit_len, npy_data):

    eh, el = hword_to_bytes(emit_len)
    #print([bytearray(chunk.tobytes()) for chunk in np.array_split(npy_data, nchunks)])
    chunks, nchunks = to_chunks(TX_DATA_FRAME, npy_data, order=2, encode=True)
    enh, enl = hword_to_bytes(nchunks)
    #chunks = [encode_msg(bytearray(chunk.byteswap(inplace=True).tobytes())) for chunk in np.array_split(npy_data, nchunks)]
    msg = encode_msg(bytearray([TX_MSG_FRAME, 0x01, eh, el, enh, enl]))
    chunks.insert(0, msg)

    return chunks, (TX_FLAG, EMITTER_FLAG)


def gen_sine(start_time, end_time, frequency):
    tvec = np.arange(start_time, end_time, 1/DAC_SAMPLING_RATE)
    
    s = (DAC_MAX_INT - 1)/2 * (1 + np.sin(2 * np.pi * frequency * tvec))
    
    return build_emit_upd(len(s), s.astype(np.uint16))
