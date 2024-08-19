import bb_serial
import time

ser = bb_serial.BB_Serial('/dev/ttyACM0')
ser.set_attributes(115200, 1)
ser.enable_blocking(True)
ser.writeBytes([0xFF, 0x05, 0x01, 0x03, 0x00, 0x00, 0x00], 7)
n, buff = ser.readBytes(100)
print("".join(map(chr, buff)))