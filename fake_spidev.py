"""
Author: Mason Lopez
Date: 2/2/2024
Purpose: spidev is only on linux (pi) so to run and develop on 
other platforms this is a fake library taht hold the same interface but does
nothing but log the information to console

    """
    
import logging

class SpiDev():
    def __init__(self):
        """this is a fake init"""
        self.mode = 0
        self.max_speed_hz = 10

    
    def open(self,bus,dev):
        logging.debug("fake open")
        
    def xfer2(data,de):
        logging.debug("fake xfer2")