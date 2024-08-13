"""Reads ADC values from the Teensy

    """

from serial import Serial
import time
import numpy as np
import os
from enum import Enum

class LISTENER_SERIAL_CMD(Enum):
    NONE = 0
    START_LISTEN = 1
    STOP_LISTEN = 2
    ACK_REQ = 3
    ACK = 4
    ERROR = 100
    
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
    
class EchoRecorder:
    
    def __init__(self, serial_obj:Serial = Serial(), channel_burst_len:np.uint16 = 1000, left_channel_first = True,sample_freq:int = 1e6) -> None:
        """Create echo listener using the serial device 

        Args:
            serial_obj (Serial): object of teensy
            channel_burst_len (np.uint16): length of left and right channel bursts. Defaults to 1000 uint16's.
        """
        
        self.teensy = serial_obj
        if serial_obj:
            self.teensy.baudrate = 480e6    # set the max speed!
            self.teensy.timeout = 0.2
        
        self.read_chunk_size = 1024     # 
        
        # ADC sampling stuff
        self.sample_freq = sample_freq
        self.sample_t = 1/self.sample_freq
        
        # for sending data over UART and reconstructing to left and right channels
        self.channel_burst_len = channel_burst_len
        self.left_channel_first = left_channel_first
    
    def check_status(self)->bool:
        if not self.teensy:
            return False

        if not self.teensy.is_open:
            self.teensy.open()
        else:
            self.teensy.close()
            self.teensy.open()
        self.teensy.write(b'A')
   
        
        if self.teensy.read().decode() == 'A':
            return True
        
        return False
    
    def connect_Serial(self,serial:Serial):
        self.teensy = serial
        self.teensy.baudrate = 480e6
        self.teensy.timeout = 0.3
        
    def disconnect_serial(self):
        try:
            self.teensy.close()
        except:
            pass
    
    def write_cmd(self,cmd:LISTENER_SERIAL_CMD)->None:
        self.teensy.write(cmd.value)
        
    
    def get_cmd(self)->LISTENER_SERIAL_CMD:
        cmd = self.teensy.read()
        if not cmd:
            return None
        
        cmd = int.from_bytes(cmd,'little')
        
        if cmd == LISTENER_SERIAL_CMD.ACK.value:
            return LISTENER_SERIAL_CMD.ACK
        
        elif cmd == LISTENER_SERIAL_CMD.ACK_REQ.value:
            return LISTENER_SERIAL_CMD.ACK_REQ
        
        elif cmd ==LISTENER_SERIAL_CMD.START_LISTEN.value:
            return LISTENER_SERIAL_CMD.START_LISTEN
        
        elif cmd == LISTENER_SERIAL_CMD.STOP_LISTEN.value:
            return LISTENER_SERIAL_CMD.STOP_LISTEN
        
        elif cmd == LISTENER_SERIAL_CMD.ERROR.value:
            return LISTENER_SERIAL_CMD.ERROR
        
        print(f"Unknown CMD {cmd}")
        return LISTENER_SERIAL_CMD.ERROR
    
    def connection_status(self,print_:bool = False)->bool:
        if not self.teensy.is_open:
            if print_: print(f"{t_colors.FAIL}LISTENER NO SERIAL!{t_colors.ENDC}") 
            try:
                if self.teensy.portstr != None:
                    self.teensy.open()
                    if not self.teensy.is_open:
                        return False
                else:
                    return False
            except:
                return False

            
        else:
            self.teensy.close()
            self.teensy.open()
            
        self.teensy.flush()
        self.teensy.write([LISTENER_SERIAL_CMD.ACK_REQ.value])
        back_val = self.get_cmd()

        if back_val == LISTENER_SERIAL_CMD.ACK:
            if print_: print(f"{t_colors.OKCYAN}LISTENER CONNECTED!{t_colors.ENDC}")
            return True
        

        if print_: print(f"LISTENER NOT RESPONDING!{back_val}")
        return False
        
    def listen(self, listen_time_ms:np.uint16)->tuple[np.uint16,np.uint16,np.uint16]:
        """Reads bytes from Teensy for given amount of listen time. This listen time
         is calculated into number of bytes so deviation of time is not an issue. The raw_data
         is interleaved between left and right ear for ease of demodulating at the end.

        Args:
            listen_time_ms (np.uint16): time to listen for in ms

        Returns:
            tuple[np.uint16,np.uint16,np.uint16]: raw_data, left_ear, right_ear
        """
        
        if not self.connection_status():
            print(f"EROR")
            return None
        
        
        listen_time_ms = listen_time_ms * 1e-3
        
        # ms * 1MS * 2 ears
        samples_to_read = int(listen_time_ms*self.sample_freq * 2)
        read_times = int(samples_to_read/self.channel_burst_len)

            
        raw_bytes = bytearray()
        self.teensy.write([LISTENER_SERIAL_CMD.START_LISTEN.value])
        for i in range(read_times):
            raw_bytes.extend(self.teensy.read(self.channel_burst_len*2))

        self.teensy.write([LISTENER_SERIAL_CMD.STOP_LISTEN.value])
        self.teensy.flush()
        self.teensy.close()
        self.teensy.open()
        self.teensy.flush()
        
        raw_data = np.frombuffer(raw_bytes,dtype=np.uint16)

        if self.left_channel_first:
            left_ear = raw_data[::2]
            right_ear = raw_data[1::2]
        else:
            left_ear = raw_data[1::2]
            right_ear = raw_data[::2]

            
        return [raw_bytes,left_ear,right_ear]

        
        
        
        
        