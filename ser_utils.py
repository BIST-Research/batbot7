#
# Author: Ben Westcott
# Date Created: 12/26/23
#

import numpy as np

SER_FRAME_START = 0x7E
SER_FRAME_END = 0x7f
SER_ESC = 0x7D
SER_XOR = 0x20

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
    
    out = [SER_FRAME_START]
    
    for n in range(0, len(msg)):
        b = msg[n]
        if b == SER_FRAME_START or b == SER_ESC:
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
# MCU sends listen data in chunks of 64 bytes, so
# if 64 doesnt divide the length, then add an
# additional chunk. When data is received,
# prune it to length
def determine_num_chunks(buflen, order=1):
    buflen = order*buflen
    nchunks = buflen // BUF_LEN
    if buflen % BUF_LEN:
        nchunks += 1
    return nchunks
    

