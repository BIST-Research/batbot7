

from serial import Serial
import time
import numpy as np
import os


class EchoEmitter:
    def __init__(self,serial_obj:Serial = Serial(),output_freq:int = 1e6) -> None:
        
        self.itsy = serial_obj
        
        
        self.output_freq = output_freq
        self.output_t = 1/output_freq
    
    def connect_Serial(self,serial:Serial):
        self.itsy = serial
        
    def connection_status(self) ->bool:
        return self.itsy.is_open
        
        
    def upload_chirp(self,data:np.uint16 = None, file:str = None)->bool:
        if not self.itsy:
            print(f"NO SERIAL")
            return False
        
        if not self.itsy.is_open:
            print(f"PORT: {self.itsy.portstr} no working")
            return False
        
    def check_chirp(self,data = None, file:str = None):
        pass
    
    def convert_chirp(self,data = None, file:str = None):
        pass
    
    def chirp(self,data = None, file:str = None):
        pass
    
    
    def gen_chirp(self,time_ar:np.uint16, f_start:int,f_end:int, t_end:int,method:str ='linear')->np.uint16:
        pass