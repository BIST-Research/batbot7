from datetime import datetime

def get_timestamp_now():
    return datetime.now().strftime('%Y%m%d_%H%M%S%f')[:-3]

def bin2dec(bin_data):
    return [((y << 8) | x) for x, y in zip(bin_data[::2], bin_data[1::2])]
    
def split_word(word):

    mask = 0x000000ff
    
    return [(word >> 24) & mask, (word >> 16) & mask, (word >> 8) & mask, (word >> 0) & mask]

# order is type of int, i.e.:
# uint8_t = 1
# uint16_t = 2
# uint32_t = 4
# uint64_t = 8
def list2bytearr(lst, order):
    byterr = bytearray()
    for num in lst:
        b = int(num).to_bytes(order, byteorder='little')
        for o in reversed(range(0, order)):
            byterr.append(b[o])
    
    return byterr

def blist2bytearr(lst, order):
    byterr = bytearray()
    for num in lst:
        b = int(num).to_bytes(order, byteorder='big')
        for o in reversed(range(0, order)):
            byterr.append(b[o])
    
    return byterr
