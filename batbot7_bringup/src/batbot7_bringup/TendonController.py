from enum import Enum

import ctypes
import os

dllURI_base_folder = os.path.join(os.path.expanduser('~'), 'batbot7', 'batbot7_bringup', 'c_lib', 'build', 'src')
dllURI = dllURI_base_folder + '/libserial.so'

lib = ctypes.cdll.LoadLibrary(dllURI)

class COM_TYPE(Enum):
    NONE = -1
    SPI = 0
    FAKE_SPI = 1
    UART = 2

class OPCODE(Enum):
    ECHO = 0
    READ_STATUS = 1
    READ_ANGLE = 2
    WRITE_ANGLE = 3
    WRITE_PID = 4


class TendonController:
    def __init__(self, com=COM_TYPE.NONE, port_name=''):

        lib.TendonHardwareInterface_new.argtypes = [ctypes.c_char_p]
        lib.TendonHardwareInterface_new.restype = ctypes.c_void_p

        lib.BuildPacket.argtypes = [ctypes.c_void_p, ctypes.c_uint8, ctypes.c_uint8, ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t]
        lib.BuildPacket.restype = ctypes.c_void_p

        lib.SendTxRx.argtypes = [ctypes.c_void_p]
        lib.SendTxRx.restype = ctypes.c_void_p

        lib.SendTx.argtypes = [ctypes.c_void_p]
        lib.SendTx.restype = ctypes.c_void_p

        self.TendonInterface = lib.TendonHardwareInterface_new(port_name.encode('utf-8'))

            

    def connectDev(self, com:COM_TYPE, port_name):
        print()

    def writeAngle(self, id, angle):
        angle_h = (angle >> 8) & 0xFF
        angle_l = angle & 0xFF

        params = [angle_h, angle_l]

        seq = ctypes.c_uint8 * len(params)
        arr = seq(*params)

        lib.BuildPacket(self.TendonInterface, id, OPCODE.WRITE_ANGLE.value, arr, len(params))
        lib.SendTx(self.TendonInterface)

    def readAngle(self, id):
        params = []

        seq = ctypes.c_uint8 * len(params)
        arr = seq(*params)

        lib.BuildPacket(self.TendonInterface, id, OPCODE.READ_ANGLE.value, arr, len(params))
        lib.SendTxRx(self.TendonInterface)

    def moveMotorToMin(self):
        print()

    def moveMotorToMax(self):
        print()

    def moveMotorToZero(self):
        print()

    def setNewZero(self):
        print()

if __name__ == "__main__":
    tc = TendonController(port_name="/dev/ttyACM0")

    tc.writeAngle(0, 90)
    # tc.readAngle(0)

"""
BUG: For some reason sending these messages first causes a freeze
"""