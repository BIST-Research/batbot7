import numpy as np

import ctypes
import os

dllURI_base_folder = os.path.join(os.path.expanduser('~'), 'batbot7', 'batbot7_bringup', 'c_lib', 'build', 'src')
dllURI = dllURI_base_folder + '/libserial.so'

lib = ctypes.cdll.LoadLibrary(dllURI)

class BB_Serial():
    def __init__(self, portName):
        lib.BB_Serial_new.argtypes = [ctypes.c_char_p]
        lib.BB_Serial_new.restype = ctypes.c_void_p

        lib.set_attributes.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
        lib.set_attributes.restype = ctypes.c_int

        lib.enable_blocking.argtypes = [ctypes.c_void_p, ctypes.c_bool]
        lib.enable_blocking.restype = ctypes.c_void_p

        lib.writeBytes.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint8), ctypes.c_int]
        lib.writeBytes.restype = ctypes.c_void_p

        lib.readBytes.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint8), ctypes.c_int]
        lib.readBytes.restype = ctypes.c_void_p

        lib.closePort.argtypes = [ctypes.c_void_p]
        lib.closePort.restype = ctypes.c_void_p

        self.serObj = lib.BB_Serial_new(portName.encode('utf-8'))

    def set_attributes(self, speed, parity):
        return lib.set_attributes(self.serObj, speed, parity)

    def enable_blocking(self, should_block):
        lib.enable_blocking(self.serObj, should_block)

    def writeBytes(self, buff, numBytes):
        seq = ctypes.c_uint8 * len(buff)
        arr = seq(*buff)

        lib.writeBytes(self.serObj, arr, numBytes)

    def readBytes(self, numBytes):
        buff = (ctypes.c_uint8 * numBytes)()

        n = lib.readBytes(self.serObj, buff, numBytes)
        
        return n, buff

    def closePort(self):
        lib.closePort(self.serObj)

    def __del__(self):
        self.closePort()