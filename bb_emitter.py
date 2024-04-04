

from serial import Serial
import time
import numpy as np
import os
from enum import Enum
import struct
import matplotlib.pyplot as plt
# plt.set_loglevel("error")


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
    CLEAR_SERIAL = 10


class EchoEmitter:
    def __init__(self,serial_obj:Serial = Serial(),output_freq:int = 1e6) -> None:
        
        self.itsy = serial_obj
        self.itsy.timeout = 3
        # self.itsy.xonxoff = False
        self.connection_status()
        
        self.max_chirp_length = None
        self.get_max_chirp_uint16_length()
        
        self.output_freq = output_freq
        self.output_t = 1/output_freq
        
        self.chirp_uploaded = False
    
    def connect_Serial(self,serial:Serial):
        self.itsy = serial
        self.itsy.timeout = 2
        self.connection_status()
        self.get_max_chirp_uint16_length()
        
    def connection_status(self,print_:bool = False) ->bool:
        if not self.itsy.is_open:
            if print_: print("EMIT NO SERIAL!") 
            try:
                if self.itsy.portstr != None:
                    self.itsy.open()
            except:
                pass
            
            return
        else:
            self.itsy.close()
            self.itsy.open()
            
        
        self.write_cmd(ECHO_SERIAL_CMD.ACK_REQ)
        back_val = self.get_cmd()

        if back_val == ECHO_SERIAL_CMD.ACK:
            if print_: print("EMIT CONNECTED!")
            return True
        

        if print_: print("EMIT NOT RESPONDING!")
        return False
    
    def write_cmd(self,cmd:ECHO_SERIAL_CMD):
        write_val = struct.pack('B',cmd.value)
        self.itsy.write(write_val)

    def get_cmd(self)->ECHO_SERIAL_CMD:
        cmd = self.itsy.read()

        if not cmd:
            return None
        
        cmd = int.from_bytes(cmd,'little')

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

    def chirp(self) -> bool:
        if not self.connection_status():
            return False
        if False == self.chirp_uploaded:
            print("WARNING NO CHRIP UPLOADED, PRECEEDING ANYWAY!")
            
        self.write_cmd(ECHO_SERIAL_CMD.EMIT_CHIRP)
        msg = self.get_cmd()
        if msg != ECHO_SERIAL_CMD.ACK:
            print(f"FAILED TO CHIRP? {msg}")
            return False

    def upload_chirp(self,data:np.uint16 = None, file:str = None)->bool:
        print("UPLOAD CHIRP")
        self.itsy.flush()
        if not self.connection_status():
            
            return False
        
        if not self.max_chirp_length:
            self.get_max_chirp_uint16_length()
        
        write_data = []
        copy_write = bytearray()
        data_len = len(data)
        
        if data_len > self.max_chirp_length:
            print(f"DATA TOO LONG! {data_len} max is {self.max_chirp_length}")
            return False

        
        
        write_data = data.tolist()
        for data in write_data:
            copy_write.append(data &0xff)
            copy_write.append((data>>8)&0xff)
        
        # self.write_cmd(ECHO_SERIAL_CMD.CHIRP_DATA)
        self.itsy.write([ECHO_SERIAL_CMD.CHIRP_DATA.value,data_len&0xff,data_len>>8&0xff])
        
    
        data = self.itsy.read(2)
        data = data[0] | data[1]<<8
        if data != data_len:
            print(f"ERROR RETURNED DIFF LENGTHS {data}")
            msg_recv = self.get_cmd()
            print(f"returned {msg_recv}")
            return False
        else:
            print(f"GOT GOOD LEN BACK")

            
        msg_recv = self.get_cmd()
        if msg_recv != ECHO_SERIAL_CMD.ACK:
            print(f"ERROR WAITING FOR ACK GOT {msg_recv}")
            self.chirp_uploaded = False
            return False
        else:
            print(f"GOT LENGTH ACK")
            

        
        
        ack_count = 0
        # for i,data in enumerate(copy_write):
        for i in range(0,len(copy_write),2):
            self.itsy.write([copy_write[i],copy_write[i+1]])
                        
                
        
        self.write_cmd(ECHO_SERIAL_CMD.ACK_REQ)
        msg_recv = self.get_cmd()
        if msg_recv != ECHO_SERIAL_CMD.ACK:
            print(f"EXPECTED ACK {msg_recv}")
            self.chirp_uploaded = False
            return
        else:
            print(f"GOT ACK")
        
        return_data = bytearray()
        for i in range(data_len):
            return_data.extend(self.itsy.read(2))
            
        print(f"Got {len(return_data)} and sent {len(copy_write)}")
        if return_data == copy_write:
            print(f"SUCCESS UPLOADED CHIRP")
        else:
            print(f"FAILED TO UPLOAD CHIRP")
            self.chirp_uploaded = False
            return False
        
        self.chirp_uploaded = True


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
        
        self.max_chirp_length = raw[0] | raw[1] <<8
        
        return self.max_chirp_length

        
    def check_chirp(self,data = None, file:str = None):
        pass
    
    def convert_chirp(self,data = None, file:str = None):
        pass
    
    def chirp(self,data = None, file:str = None):
        pass
    
    
    def gen_chirp(selff_start:int,f_end:int, t_end:int,method:str ='linear')->np.uint16:
        pass
    
    def gen_sine(self,time_ms:np.uint16, freq:np.uint16)->tuple[np.uint16,np.ndarray]:
        if time_ms > 60:
            print(f"time {time} too large!")
            return
        
        DATA_LEN = int(time_ms*1e3)
        duration = DATA_LEN / 1e6  # Duration of the sine wave (in seconds)
        
        t = np.linspace(0, duration, DATA_LEN, endpoint=False)
        
        sin_wave = 1 + np.sin(2 * np.pi * freq *t)
        sin_wave = sin_wave*2000
        sin_wave = sin_wave.astype(np.uint16)
        
        return [sin_wave,t]

if __name__ == '__main__':
    emitter = EchoEmitter(Serial('/dev/tty.usbmodem14101',baudrate=960000))

    DATA_LEN = 30000
    


    frequency = 10e3  # Frequency of the sine wave (in Hz)
    sample_rate = 1000000  # Sampling rate (number of samples per second)
    duration = DATA_LEN / sample_rate  # Duration of the sine wave (in seconds)

    # Generate time values
    # t = np.linspace(0, duration, DATA_LEN, endpoint=False)

    # Generate sine wave values
    # sin_wave = 1+np.sin(2 * np.pi * frequency * t)
    # sin_wave = sin_wave*2000
    # sin_wave = sin_wave.astype(np.uint16)
    
    sin_wave,t = emitter.gen_sine(40,30e3)

    plt.figure()
    plt.plot(t,sin_wave,'o-')

    plt.show()

    print(f"len {len(t)} len {len(sin_wave)}")

    emitter.upload_chirp(sin_wave)

    # emitter.write_cmd(ECHO_SERIAL_CMD.EMIT_CHIRP)
    # emitter.write_cmd(ECHO_SERIAL_CMD.EMIT_CHIRP)
    # emitter.write_cmd(ECHO_SERIAL_CMD.EMIT_CHIRP)
    # emitter.write_cmd(ECHO_SERIAL_CMD.EMIT_CHIRP)

