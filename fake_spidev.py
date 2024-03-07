"""
Author: Mason Lopez
Date: 2/2/2024
Purpose: spidev is only on linux (pi) so to run and develop on 
other platforms this is a fake library taht hold the same interface but does
nothing but log the information to console

    """
    
import logging
import numpy as np

class fake_SpiDev():
    def __init__(self):
        """this is a fake init"""
        self.mode = 0
        self.max_speed_hz = 10

    
    def open(self,bus,dev):
        logging.debug("fake open")
        
    def xfer2(de,data:list):
        logging.debug("fake xfer2")
        chunked_data = np.zeros(8, dtype=np.int16)
        index = 1
        chunked_data[0]= data[0]

        # view the bytes being sent
        for i, item in enumerate(data):
            if i > 0:
                if i % 2 == 0:
                    chunked_data[index] |= item
                    index +=1
                else:
                    chunked_data[index] = (item << 8)
        print(chunked_data)
