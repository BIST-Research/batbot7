#
# Date created: 4/3/23
# Author: Ben Westcott
#

import serial
import serial.tools.list_ports
import logging
import sys
import time

def search_comports(serial_numbers):

    for port in serial.tools.list_ports.comports():
        for serial_number in serial_numbers:
            if type(port.serial_number) != str:
                continue
            if port.serial_number == serial_number:
                return port
    return "None"

class M4:
    
    def __init__(self, serial_numbers, baud_rate, bat_log):
    
                
        self.port = search_comports(serial_numbers)
        self.bat_log = bat_log
        
        
        if str(self.port) == "None":
            self.bat_log.critical(f"Could not find any devices with the listed serial numbers!")
            exit()
            
            
        self.device = serial.Serial(self.port.device, baud_rate)
        
        bat_log.info(f"[Serial] Found {self.port.serial_number} on {self.port.device}")

        #self.reset()
        
    def reset(self):

        self.device.setDTR(False)
        
        time.sleep(1)
        
        self.device.flushInput()
        self.device.setDTR(True)
    
    def write(self, packet):
        self.device.write(packet)
    
    def read(self, length):
        return self.device.read(length)
        
    def in_waiting(self):
        return self.device.inWaiting()
