

from serial import Serial
import time
import numpy as np
import os
from enum import Enum
import struct
import matplotlib.pyplot as plt
import sys
from scipy import signal


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

def hide_cursor():
    sys.stdout.write("\033[?25l")  # Hide cursor
    sys.stdout.flush()

def show_cursor():
    sys.stdout.write("\033[?25h")  # Show cursor
    sys.stdout.flush()

class t_colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


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
            if print_: print(f"{t_colors.FAIL}EMIT NO SERIAL!{t_colors.ENDC}") 
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
            if print_: print(f"{t_colors.OKCYAN}EMIT CONNECTED!{t_colors.ENDC}")
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
        
        print(f"{t_colors.FAIL}UNKNOWN CMD {cmd}{t_colors.ENDC}")
        return ECHO_SERIAL_CMD.ERROR

    def chirp(self) -> bool:
        if not self.connection_status():
            return False
        if False == self.chirp_uploaded:
            print(f"{t_colors.WARNING}WARNING NO CHRIP UPLOADED, PRECEEDING ANYWAY!{t_colors.ENDC}")
            
        self.write_cmd(ECHO_SERIAL_CMD.EMIT_CHIRP)
        msg = self.get_cmd()
        if msg != ECHO_SERIAL_CMD.ACK:
            print(f"{t_colors.FAIL}FAILED TO CHIRP {msg}{t_colors.ENDC}")
            return False

    def upload_chirp(self,data:np.uint16 = None, file:str = None,verify:bool = True)->bool:
        self.itsy.flush()
        if not self.connection_status():
            
            return False
        
        if not self.max_chirp_length:
            self.get_max_chirp_uint16_length()
        
        write_data = []
        copy_write = bytearray()
        data_len = len(data)
        
        if data_len > self.max_chirp_length:
            print(f"{t_colors.FAIL}DATA TOO LONG! {data_len} max is {self.max_chirp_length}{t_colors.ENDC}")
            return False

        
        
        write_data = data.tolist()
        for data in write_data:
            copy_write.append(data &0xff)
            copy_write.append((data>>8)&0xff)
        
        self.itsy.write([ECHO_SERIAL_CMD.CHIRP_DATA.value,data_len&0xff,data_len>>8&0xff])
        
    
        data = self.itsy.read(2)
        data = data[0] | data[1]<<8
        if data != data_len:
            print(f"{t_colors.FAIL}ERROR RETURNED DIFF LENGTHS {data}{t_colors.ENDC}")
            msg_recv = self.get_cmd()
            print(f"returned {msg_recv}")
            return False

            
        msg_recv = self.get_cmd()
        if msg_recv != ECHO_SERIAL_CMD.ACK:
            print(f"ERROR WAITING FOR ACK GOT {msg_recv}")
            self.chirp_uploaded = False
            return False
            
        # upload the chirp
        hide_cursor()
        for i in range(0,len(copy_write),2):
            self.itsy.write([copy_write[i],copy_write[i+1]])
            
            if i % 50 == 0:
                print(f"{t_colors.OKBLUE}Uploading{t_colors.ENDC}: {i/len(copy_write)*100:.1f}%",end='\r',flush=True)
        print(f"{t_colors.OKBLUE}Uploading{t_colors.ENDC}: {100:.1f}%",end='\r',flush=True)
        print()            
        show_cursor()
                
        # wait for an ack from itsy to say they got it
        self.write_cmd(ECHO_SERIAL_CMD.ACK_REQ)
        msg_recv = self.get_cmd()
        if msg_recv != ECHO_SERIAL_CMD.ACK:
            print(f"{t_colors.FAIL}EXPECTED ACK {msg_recv}{t_colors.ENDC}")
            self.chirp_uploaded = False
            return
        
        # verify the chirp by reading it back
        print("Validating data..")
        hide_cursor()
        return_data = bytearray()
        for i in range(int(data_len/2)):
            return_data.extend(self.itsy.read(4))
            if i % 50 == 0:
                print(f"{t_colors.OKBLUE}Reading{t_colors.ENDC}: {i*2/data_len*100:.1f}%",end='\r',flush=True)
        print(f"{t_colors.OKBLUE}Reading{t_colors.ENDC}: {100:.1f}%",end='\r',flush=True)
        print()
        show_cursor()

        if return_data == copy_write:
            print(f"{t_colors.OKGREEN}SUCCESS, UPLOADED CHIRP!{t_colors.ENDC}")
        else:
            print(f"{t_colors.FAIL}FAILED TO UPLOAD CHIRP{t_colors.ENDC}")
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
    
    
    def gen_chirp(self,f_start:int,f_end:int, t_end:int,method:str ='linear')->tuple[np.uint16,np.ndarray]:
        if t_end > 60:
            print(f"{t_colors.FAIL}time {time} too large!{t_colors.ENDC}")
            return
        
        Fs = 1e6
        Ts = 1/Fs
        t = np.arange(0,t_end*1e-3 - Ts/2,Ts)
        chirp = signal.chirp(t,f_start,t_end*1e-3,f_end,method)
        chirp = chirp + 1
        chirp = chirp*2040

        chirp = chirp.astype(np.uint16)

        return [chirp,t]
    
    def gen_sine(self,time_ms:np.uint16, freq:np.uint16)->tuple[np.uint16,np.ndarray]:
        if time_ms > 60:
            print(f"{t_colors.FAIL}time {time} too large!{t_colors.ENDC}")
            return
        
        DATA_LEN = int(time_ms*1e3)
        duration = DATA_LEN / 1e6  # Duration of the sine wave (in seconds)
        
        t = np.linspace(0, duration, DATA_LEN, endpoint=False)
        
        sin_wave = 1 + np.sin(2 * np.pi * freq *t)
        sin_wave = sin_wave*2040
        sin_wave = sin_wave.astype(np.uint16)
        
        return [sin_wave,t]

if __name__ == '__main__':
    emitter = EchoEmitter(Serial('COM5',baudrate=960000))

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
    
    # sin_wave,t = emitter.gen_sine(40,30e3)
    sin_wave, t = emitter.gen_chirp(90e3,40e3,30)

    plt.figure()
    plt.plot(t,sin_wave,'o-')

    plt.show()

    print(f"len {len(t)} len {len(sin_wave)}")

    # emitter.upload_chirp(sin_wave)

    # emitter.write_cmd(ECHO_SERIAL_CMD.EMIT_CHIRP)
    # emitter.write_cmd(ECHO_SERIAL_CMD.EMIT_CHIRP)
    # emitter.write_cmd(ECHO_SERIAL_CMD.EMIT_CHIRP)
    # emitter.write_cmd(ECHO_SERIAL_CMD.EMIT_CHIRP)

