#
# Author: Ben Westcott
# Date Created: 1/20/24
#

import numpy as np

from bb_utils import *
from ser_utils import *

TEST_EMIT_UPD_MSG = [TX_MSG_FRAME, 0x01, 0x0b, 0xb8, 0x00, 0x18]

EMIT_VALIDATE_LENGTH = 0b00000001
EMIT_VALIDATE_DAC_BOUNDS = 0b00000010
EMIT_VALIDATE_STRENGTH = 0b00000100

#def validate_emit_upd()

def build_emit_upd(emit_len, npy_data):

    eh, el = hword_to_bytes(emit_len)

    nchunks = determine_num_chunks(emit_len, order=2)
    enh, enl = hword_to_bytes(nchunks)

    chunks = [encode_msg(bytearray(chunk.tobytes())) for chunk in np.array_split(npy_data, nchunks)]

    msg = encode_msg(bytearray([TX_MSG_FRAME, eh, el, enh, enl]))

    chunks.insert(0, msg)

    return chunks, (TX_FLAG, TX_EMITTER_FLAG)

