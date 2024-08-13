

from serial import Serial
import time
import numpy as np
import os
from enum import Enum
import struct
import matplotlib.pyplot as plt
import sys
from scipy import signal
import zlib



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
    
class LAST_CHIRP_DATA(Enum):
    FILE = 0
    CUSTOM = 1
    NONE = 3

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
        self.itsy.timeout = 0.5
        # self.itsy.xonxoff = False
        self.connection_status()
        
        self.max_chirp_length = None
        self.get_max_chirp_uint16_length()
        
        self.output_freq = output_freq
        self.output_t = 1/output_freq
        
        self.chirp_uploaded = False
        self.last_upload_type = LAST_CHIRP_DATA.NONE
        self.last_f0 = 0
        self.last_f1 = 0
        self.last_tend = 0
        self.last_method = 0
        self.last_filename = ""
        
        self.SIG_GAIN = 512
        self.SIG_OFFSET = 2048
        
        self.EMIT_TIME = 0
    
    def connect_Serial(self,serial:Serial):
        self.itsy = serial
        self.itsy.timeout = 0.5
        self.connection_status()
        self.get_max_chirp_uint16_length()
        

        
    def disconnect_serial(self):
        try:
            self.itsy.close()
        except:
            pass
        
        
    def connection_status(self,print_:bool = False) ->bool:
        if not self.itsy.is_open:
            if print_: print(f"{t_colors.FAIL}EMIT NO SERIAL!{t_colors.ENDC}") 
            try:
                if self.itsy.portstr != None:
                    self.itsy.open()
                    if not self.itsy.is_open:
                        return False
                else:
                    return False
            except:
                return False
                
            
        else:
            self.itsy.close()
            self.itsy.open()
            
        
        # self.write_cmd(ECHO_SERIAL_CMD.ACK_REQ)
        self.itsy.write([ECHO_SERIAL_CMD.ACK_REQ.value])
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

    def upload_chirp(self,data:np.uint16 = None)->bool:
        self.itsy.flush()
        if not self.connection_status():
            return False
        
        if not self.max_chirp_length:
            self.get_max_chirp_uint16_length()
        
        write_data = []
        copy_write = bytearray()
        data_len = len(data)
        
        if data_len > self.max_chirp_length:
            print(f"{t_colors.FAIL}DATA TOO LONG! given: {data_len} but max is {self.max_chirp_length} or {self.max_chirp_length*1e-3}ms!{t_colors.ENDC}")
            return False

        
        OG_CRC = zlib.crc32(data)

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
        for i in range(0,len(copy_write),20):
            self.itsy.write([copy_write[i],copy_write[i+1],
                             copy_write[i+2],copy_write[i+3],
                             copy_write[i+4],copy_write[i+5],
                             copy_write[i+6],copy_write[i+7],
                             copy_write[i+8],copy_write[i+9],
                             copy_write[i+10],copy_write[i+11],
                             copy_write[i+12],copy_write[i+13],
                             copy_write[i+14],copy_write[i+15],
                             copy_write[i+16],copy_write[i+17],
                             copy_write[i+18],copy_write[i+19]])
            
            if i % 20 == 0:
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
        print("Validating hash...")
        crc_back = self.itsy.read(4)
        crc_back = (crc_back[0] | (crc_back[1]<<8) | (crc_back[2] << 16) | (crc_back[3] << 24))


        if crc_back == OG_CRC:
            print(f"{t_colors.OKGREEN}SUCCESS, UPLOADED CHIRP!{t_colors.ENDC}")
        else:
            print(f"{t_colors.FAIL}FAILED TO UPLOAD CHIRP{t_colors.ENDC}")
            self.chirp_uploaded = False
            return False
        
        self.chirp_uploaded = True
        self.EMIT_TIME = data_len

 
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

    
    
    def gen_chirp(self,f_start:int,f_end:int, t_end:int,method:str ='linear',gain:float = None,offset = None)->tuple[np.uint16,np.ndarray]:
        Fs = 1e6
        Ts = 1/Fs
        t = np.arange(0,t_end*1e-3 - Ts/2,Ts)
        chirp = signal.chirp(t,f_start,t_end*1e-3,f_end,method)
        chirp = self.convert_and_range_data(chirp,gain,offset)

        self.last_upload_type = LAST_CHIRP_DATA.CUSTOM
        self.last_f0 = f_start
        self.last_f1 = f_end
        self.last_tend = t_end
        self.last_method = method
        
        return [chirp,t]
    
    def gen_sine(self,time_ms:np.uint16, freq:np.uint16,gain:float = None,offset = None)->tuple[np.uint16,np.ndarray]:
        DATA_LEN = int(time_ms*1e3)
        duration = DATA_LEN / 1e6  # Duration of the sine wave (in seconds)
        
        t = np.linspace(0, duration, DATA_LEN, endpoint=False)
        
        sin_wave = np.sin(2 * np.pi * freq *t)
        sin_wave = self.convert_and_range_data(sin_wave,gain,offset)
        
        self.last_upload_type = LAST_CHIRP_DATA.CUSTOM
        self.last_f0 = freq
        self.last_f1 = freq
        self.last_tend = time_ms
        self.last_method = 'Sine wave'
        
        return [sin_wave,t]
    
    def convert_and_range_data(self,data:np.ndarray,gain:float = None,offset:float =None)->np.uint16:
        data = data - np.min(data)
        data = data/np.max(data)
        
        g = self.SIG_GAIN
        if gain is not None:
            g = gain
        
        of = self.SIG_OFFSET
        if offset is not None:
            of = offset
            
        data = data*g + of
        

        return data.astype(np.uint16)
    
    def get_and_convert_numpy(self,file_name:str,gain:float = None,offset = None)->np.uint16:
        if not os.path.exists(file_name):
            print(f"File does not exist!")
            return None
        data = np.load(file_name)
        data = self.convert_and_range_data(data,gain,offset)
        
        self.last_upload_type = LAST_CHIRP_DATA.FILE
        self.last_filename = file_name
        return data

    def save_chirp_info(self,file_path:str)->bool:
        if not file_path.endswith(".txt"):
            file_path += ".txt"
            
        with open(file_path,"w") as f:
            f.write(f"ECHO_DATA:\n")
            if self.last_upload_type == LAST_CHIRP_DATA.CUSTOM:
                f.write(f"START FREQ: {self.last_f0} END FREQ: {self.last_f1} DURATION MS: {self.last_tend} METHOD: {self.last_method}\n")
            elif self.last_upload_type == LAST_CHIRP_DATA.FILE:
                f.write(f"FILE USED: {self.last_filename}")
            else:
                f.write(f"WARNING UNKNOWN CHIRP!!\n")
                return False
        
        return True
        






if __name__ == '__main__':
    emitter = EchoEmitter(Serial('COM5',baudrate=960000))




    sin_wave, t = emitter.gen_chirp(90e3,40e3,30)

    np.save('sine_uint16.npy',sin_wave)

    DATA_LEN = int(30*1e3)
    duration = DATA_LEN / 1e6  # Duration of the sine wave (in seconds)
        
    t = np.linspace(0, duration, DATA_LEN, endpoint=False)
        
    d1 = np.sin(2 * np.pi * 50e3 *t)
    np.save('sine_float.npy',d1)


    check_and_get_numpy_file('sine_uint16.npy')

    clean = check_and_get_numpy_file('sine_float.npy')

    plt.figure()
    plt.subplot(1,2,1)
    plt.plot(d1,'o-')
    plt.xlim([0 ,200])

    plt.subplot(1,2,2)
    plt.plot(clean,'o-')
    plt.xlim([0, 200])
    plt.show()


    # emitter.upload_chirp(sin_wave)


