from datetime import datetime
import serial

def get_timestamp_now():
    return datetime.now().strftime('%Y%m%d_%H%M%S%f')[:-3]

def bin2dec(bin_data):
    return [((y << 8) | x) for x, y in zip(bin_data[::2], bin_data[1::2])]
    
def split_word(word):
    mask = 0x000000ff
    return [(word >> 24) & mask, (word >> 16) & mask, (word >> 8) & mask, (word >> 0) & mask]
    
def hword_to_bytes(word):
    return (word >> 8) & 0xFF, word & 0xFF

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

def search_comports(serial_numbers):

    for port in serial.tools.list_ports.comports():
    
        for serial_number in serial_numbers:
            
            if type(port.serial_number) != str:
                continue
        
            if port.serial_number == serial_number:
                return port
    
    return None


