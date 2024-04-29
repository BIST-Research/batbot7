"""Reads ADC values from the Teensy

    """

from serial import Serial
import time
import numpy as np
import os


    
class EchoListener:
    
    def __init__(self,serial_obj:Serial,channel_burst_len:np.uint16 = 1000, left_channel_first = True,sample_freq:int = 1e6) -> None:
        """Create echo listener using the serial device 

        Args:
            serial_obj (Serial): object of teensy
            channel_burst_len (np.uint16): length of left and right channel bursts. Defaults to 1000 uint16's.
        """
        self.teensy = serial_obj
        self.teensy.baudrate = 480e6    # set the max speed!
        self.teensy.timeout = 0.1
        
        self.read_chunk_size = 1024     # 
        
        # ADC sampling stuff
        self.sample_freq = sample_freq
        self.sample_t = 1/self.sample_freq
        
        # for sending data over UART and reconstructing to left and right channels
        self.channel_burst_len = channel_burst_len
        self.left_channel_first = left_channel_first
    
    def check_status(self)->bool:
        self.teensy.flush()
        self.teensy.write(b'0')
        self.teensy.write(b'A')
        
        
        if self.teensy.read().decode() == 'A':
            return True
        
        return False
        
    def listen(self, listen_time_ms:np.uint16)->tuple[np.uint16,np.uint16,np.uint16]:
        """Records data from Teensy for desired time and saves data to file as bytes.

        Args:
            file_name (str): name of binary file
            listen_time_us (np.uint16): time to listen in ms

        Returns:
            np.uint16: raw data 
        """
        
        if not self.check_status():
            print("ERROR NO ACK")
            return
        
        listen_time_ms = listen_time_ms * 1e-3
        
        # ms * 1MS * 2 ears
        samples_to_read = int(listen_time_ms*self.sample_freq * 2)
        
        read_times = int(samples_to_read/self.channel_burst_len)

            
        raw_bytes = bytearray()        
        self.teensy.write(b'1')
        for i in range(read_times):
            raw_bytes.extend(self.teensy.read(self.channel_burst_len*2))
        self.teensy.write(b'0')
            
        raw_data = np.frombuffer(raw_bytes,dtype=np.uint16)

        left_ear = raw_data[::2]
        right_ear = raw_data[1::2]
        
        return [raw_data,left_ear,right_ear]

        
        
        
        
        