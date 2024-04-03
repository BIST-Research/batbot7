

from serial import Serial
import time
import numpy as np
import os
from enum import Enum
import struct
import matplotlib.pyplot as plt

class ECHO_SERIAL_CMD(Enum):
    NONE = 0
    EMIT_CHIRP = 1
    CHIRP_DATA = 2
    ACK_REQ = 3
    ACK = 4
    ERROR = 100
    CHIRP_DATA_TOO_LONG = 6
    GET_MAX_UINT16_CHIRP_LEN = 7
    START_AMP = 8
    STOP_AMP = 9


class EchoEmitter:
    def __init__(self,serial_obj:Serial = Serial(),output_freq:int = 1e6) -> None:
        
        self.itsy = serial_obj
        self.itsy.timeout = 1
        self.connection_status()
        
        self.output_freq = output_freq
        self.output_t = 1/output_freq
    
    def connect_Serial(self,serial:Serial):
        self.itsy = serial
        self.itsy.timeout = 1
        
    def connection_status(self) ->bool:
        if not self.itsy.is_open:
            print("EMIT NO SERIAL!")
            return False
        
        self.write_cmd(ECHO_SERIAL_CMD.ACK_REQ)
        
        back_val = self.get_cmd()

        if back_val == ECHO_SERIAL_CMD.ACK:
            print("EMIT CONNECTED!")
            return True
        

        print("EMIT NOT RESPONDING!")
        return False
    
    def write_cmd(self,cmd:ECHO_SERIAL_CMD):
        write_val = struct.pack('B',cmd.value)
        self.itsy.write(write_val)

    def get_cmd(self)->ECHO_SERIAL_CMD:
        cmd = self.itsy.read()

        if not cmd:
            return None
        
        cmd = int.from_bytes(cmd,'big')

        if cmd == ECHO_SERIAL_CMD.ACK.value:
            return ECHO_SERIAL_CMD.ACK
        
        elif cmd == ECHO_SERIAL_CMD.CHIRP_DATA.value:
            return ECHO_SERIAL_CMD.CHIRP_DATA
        
        elif cmd == ECHO_SERIAL_CMD.ACK_REQ.value:
            return ECHO_SERIAL_CMD.ACK_REQ
        
        elif cmd == ECHO_SERIAL_CMD.ERROR.value:        
            return ECHO_SERIAL_CMD.ERROR
        
        elif cmd == ECHO_SERIAL_CMD.CHIRP_DATA_TOO_LONG.value:
            return ECHO_SERIAL_CMD.CHIRP_DATA_TOO_LONG
        
        elif cmd == ECHO_SERIAL_CMD.GET_MAX_UINT16_CHIRP_LEN.value:
            return ECHO_SERIAL_CMD.GET_MAX_UINT16_CHIRP_LEN

        elif cmd == ECHO_SERIAL_CMD.START_AMP.value:
            return ECHO_SERIAL_CMD.START_AMP
        
        elif cmd == ECHO_SERIAL_CMD.STOP_AMP.value:
            return ECHO_SERIAL_CMD.STOP_AMP
        
        print(f"UNKNOWN CMD {cmd}")
        return ECHO_SERIAL_CMD.ERROR


    def upload_chirp(self,data:np.uint16 = None, file:str = None)->bool:
        print("UPLOAD CHIRP")
        if not self.connection_status():
            return False
        
        write_data = []
        data_len = len(data)
        write_data.append(ECHO_SERIAL_CMD.CHIRP_DATA.value)
        write_data.append(data_len&0xff)
        write_data.append(data_len >> 8&0xff)
        for i in data:
            write_data.append(i&0xff)
            write_data.append(i >>8 &0xff)


        self.itsy.write(write_data)

        msg = self.get_cmd()

        print(f" {msg}")
        data = self.itsy.read(2)
        data_len = int.from_bytes(data,byteorder='little')
        print(f"data {data_len}")

        databack = []
        timeout_count = 0
        for i in range(data_len):
            databack.extend(self.itsy.read(2))
        

        if databack == write_data[3:]:
            print(F"SUCCESS")
        else:
            print(F"fail   og {len(write_data[3:])} real {len(databack)} ")
            print(f"class {type(write_data)} {type(databack)} ")


    def get_max_chirp_uint16_length(self) -> np.uint16:
        if not self.connection_status():
            return False
        
        self.write_cmd(ECHO_SERIAL_CMD.GET_MAX_UINT16_CHIRP_LEN)
        msg_type = self.get_cmd()

        if msg_type != ECHO_SERIAL_CMD.GET_MAX_UINT16_CHIRP_LEN:
            print(f"ITSY RETURNED {msg_type}")
            return 0
        
        raw = self.itsy.read(2)
        if not raw:
            print("TIMEOUT")
            return 0
        
        return int.from_bytes(raw,byteorder='little')

        
    def check_chirp(self,data = None, file:str = None):
        pass
    
    def convert_chirp(self,data = None, file:str = None):
        pass
    
    def chirp(self,data = None, file:str = None):
        pass
    
    
    def gen_chirp(self,time_ar:np.uint16, f_start:int,f_end:int, t_end:int,method:str ='linear')->np.uint16:
        pass

if __name__ == '__main__':
    emitter = EchoEmitter(Serial('COM5',baudrate=460000))
    stat = emitter.connection_status()
    if stat:
        print("OK")
    else:
        print("fail")

    print(F"Max buffer length {emitter.get_max_chirp_uint16_length()}")

    DATA_LEN = 60000
    


    frequency = 1e3  # Frequency of the sine wave (in Hz)
    sample_rate = 1000000  # Sampling rate (number of samples per second)
    duration = DATA_LEN / sample_rate  # Duration of the sine wave (in seconds)

    # Generate time values
    t = np.linspace(0, duration, DATA_LEN, endpoint=False)

    # Generate sine wave values
    sin_wave = 1+np.sin(2 * np.pi * frequency * t)
    sin_wave = sin_wave*2000
    sin_wave = sin_wave.astype(np.uint16)

    # plt.figure()
    # plt.plot(t,sin_wave,'o-')

    # plt.show()

    print(f"len {len(t)} len {len(sin_wave)}")

    # emitter.upload_chirp(sin_wave)

    emitter.write_cmd(ECHO_SERIAL_CMD.EMIT_CHIRP)
    # emitter.write_cmd(ECHO_SERIAL_CMD.EMIT_CHIRP)
    # emitter.write_cmd(ECHO_SERIAL_CMD.EMIT_CHIRP)
    # emitter.write_cmd(ECHO_SERIAL_CMD.EMIT_CHIRP)

