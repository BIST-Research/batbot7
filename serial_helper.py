import serial
import serial.tools.list_ports


def get_port_from_serial_num(serial_str:str)->str:
    for port in serial.tools.list_ports.comports():
        if serial_str == port.serial_number:
            return port.device
        
    return None