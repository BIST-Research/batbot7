#
# Author: Ben Westcott
# Date Created: 12/26/23
#

import numpy as np

SER_FRAME_START = 0x7E
SER_FRAME_END = 0x7f
SER_ESC = 0x7D
SER_XOR = 0x20

USART_BAUD = 460800

TX_ERR = 0x40
TX_NONE = 0x41
TX_MSG_FRAME = 0x42
TX_DATA_FRAME = 0x43

TX_FLAG = 0x50
RX_FLAG = 0x51
EMITTER_FLAG = 0x10
RECORDER_FLAG = 0x11

TX_EMITTER_FLAG = (TX_FLAG << 8) | EMITTER_FLAG
RX_EMITTER_FLAG = (RX_FLAG << 8) | EMITTER_FLAG

TX_RECORDER_FLAG = (TX_FLAG << 8) | RECORDER_FLAG
RX_RECORDER_FLAG = (RX_FLAG << 8) | RECORDER_FLAG

# bytes
BUF_LEN = 256
RAW_BUF_LEN = 515

def pad_msg(msg):
    space = RAW_BUF_LEN - len(msg)
    if space < 0:
        msg = msg[0:BUF_LEN]
    elif space > 0:
        msg.extend(list(np.zeros(space, np.byte)))
    return msg
    
def encode_msg(msg):
    #msg = pad_msg(msg)
    
    out = bytearray()
    out.append(SER_FRAME_START)
    
    for n in range(0, len(msg)):
        b = msg[n]
        if b == SER_FRAME_START or b == SER_ESC or b==SER_FRAME_END:
            out.append(SER_ESC)
            out.append(b ^ SER_XOR)
        else:
            out.append(b)
    
    out.append(SER_FRAME_END)
    return pad_msg(out)

def decode_msg(msg):

    ACCEPT = 0x01
    ESCAPE = 0x02

    state = ACCEPT
    
    decoded = bytearray()
    escape = False
    if msg[0] != SER_FRAME_START:
        return None
    del msg[0]

    frame_type = msg[0]
    del msg[0]

    for n in msg:
        if state == ACCEPT:
            if n == SER_FRAME_START:
                return None
            if n == SER_FRAME_END:
                break
            if n == SER_ESC:
                state = ESCAPE
            else:
                decoded.append(n)
            continue

        if state == ESCAPE:
            decoded.append(n ^ SER_XOR)
            state = ACCEPT
            continue
    
    return frame_type, decoded          
        
# order = 1 = sizof(uint8_t)
# order = 2 = sizeof(uint16_t)
# ...
def determine_num_chunks(buflen, order=1):
    buflen = order*buflen
    nchunks = buflen // BUF_LEN
    if buflen % BUF_LEN:
        nchunks += 1
    return nchunks
    
def chunk_split(data, size):
    return np.split(data, np.arange(size, len(data), size))
    
def to_chunks(ftype, data, order=1, encode=True):
    chunks = []
    for chunk in chunk_split(data, BUF_LEN//order):
        c = bytearray(chunk)
        c.insert(0, ftype)

        if encode:
            c = encode_msg(c)
        chunks.append(c)
    
    return chunks, determine_num_chunks(len(data), order=order)



