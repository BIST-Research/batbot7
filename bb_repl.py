"""
    About: 
        This is the main program for the batbot system. This program
        acts like a REPL, or command like interface that requires the user to 
        input commands. The user can query and command for the system
    
    Author: 
        Mason Lopez 
    
    Date: 
        March 4th 2024
    """

from cmd2 import (
    Cmd,
    with_argparser,
    DEFAULT_SHORTCUTS,
    Settable,
    Statement,
    Cmd2ArgumentParser,

)
import sys
import argparse
import struct
import pinnae
import numpy as np
import bb_listener
import bb_emitter
import yaml
import serial
import bb_gps
import matplotlib.pylab as plt
import logging
import serial.tools.list_ports
from PyQt6.QtWidgets import QApplication, QWidget

logging.basicConfig(level=logging.WARNING)
plt.set_loglevel("error")

INT16_MIN = np.iinfo(np.int16).min
INT16_MAX = np.iinfo(np.int16).max

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

def get_serial_port_from_serial_number(serial_str:str)->str:
    """Given a serial_number, function will look for open serial ports


    Args:
        serial_str (str): serial number of device

    Returns:
        str: COMx of device
    """
    for port in serial.tools.list_ports.comports():
        if serial_str == port.serial_number:
            return port.device
    return None
    

def convert_khz(hz_str:str)->float:
    freqstr = hz_str.lower()
    val = freqstr.split('k')
    if not val[0].isdigit():
        return None
    
    if freqstr.endswith('k'):
        freq = float(val[0])*1e3
    else:
        freq = float(val[0])
    return freq

def gen_fft(data)->tuple[np.ndarray,np.ndarray]:
    N = len(data)
    X = np.fft.fft(data)
    freqs = np.fft.fftfreq(N,d=1/1e6)

    return[X,freqs]

class bb_repl(Cmd):
    """BatBot 7's repl interface class
    """
    

    
    def __init__(self,yaml_cfg_file:str = 'bb_conf.yaml'):
        
        self.prompt='(batbot)>> '
        self.yaml_cfg_file = yaml_cfg_file

        self.record_MCU = bb_listener.EchoRecorder()
        self.emit_MCU = bb_emitter.EchoEmitter()
        self.L_pinna_MCU = pinnae.PinnaeController()
        self.R_pinna_MCU = pinnae.PinnaeController()
        self.gps_MCU = bb_gps.bb_gps2()
        
        
        super().__init__()
        self._startup()
        

    
    def _startup(self):
        
        
        with open(self.yaml_cfg_file, "r") as f:
            # Load YAML data
            self.bb_config = yaml.safe_load(f)
        
        self.poutput(f"{t_colors.WARNING}Checking system...{t_colors.ENDC}")
    
            
        
        self.do_status(None)
        self.do_config('')
        
                
    def do_batt(self, _:Statement) ->None: 
        """Returns the battery status of batbot
        """
        self.poutput('11.7v')
        
    def do_temp(self, _:Statement)->None:
        """Returns the temperature of the batbot
        """
        self.poutput('73f OK')
    
    pinna_parser = Cmd2ArgumentParser()
    pinna_parser.add_argument('-g','--gui',action='store_true')
    @with_argparser(pinna_parser)
    def do_pinna(self,args):
        if args.gui:
            self.app = QApplication.instance()  # Try to get the existing instance of QApplication
            if self.app is None:  # Create a new QApplication if it doesn't exist
                self.app = QApplication([])
            widget = pinnae.PinnaWidget(self.L_pinna_MCU,self.R_pinna_MCU)
            widget.show()

            self.app.exec()
            
        

    
    config_parser = Cmd2ArgumentParser()
    config_parser.add_argument('-e','--emit_MCU',action='store_true',help="config emit board")
    config_parser.add_argument('-r','--record_MCU',action='store_true',help="config record board")
    config_parser.add_argument('-lp','--left_pinna_MCU',action='store_true',help='config left pinna')
    config_parser.add_argument('-rp','--right_pinna_MCU',action='store_true',help='config right pinna')
    config_parser.add_argument('-g','--gps_MCU',action='store_true',help='config gps com')
    @with_argparser(config_parser)
    def do_config(self,args):
        """config the communication port.

        Args:
            args (_type_): which peripherral to configure.
        """


        name = ''
        if args.emit_MCU:
            name = ' for emit_MCU'
        elif args.record_MCU:
            name = ' for record_MCU'
        elif args.left_pinna_MCU:
            name = ' for left_pinna'
        elif args.right_pinna_MCU:
            name = ' for left_pinna'
        elif args.gps_MCU:
            name = ' for left_pinna'


        self.poutput(f"Searching for available serial ports{t_colors.OKBLUE}{name}{t_colors.ENDC}:")

        # Get a list of available serial ports
        ports = serial.tools.list_ports.comports()
    
        for i,port in enumerate(ports):
            self.poutput(f"{i}. Name: {port.device}\tSerial Number: {port.serial_number}")
        
        if len(name) == 0 or len(ports) == 0:
            return
        num = self.read_input(f"Choose [0,{len(ports)-1}]: ")
        while True:
            if num.isdigit() and int(num) <= len(ports)-1 and int(num) >= 0:
                break
            num = self.read_input(f"Choose [0,{len(ports)-1}]: ")
        num = int(num)
        self.poutput(f"Trying to connect to: {ports[num].device}...")
        
        failed = False
        
        name = name.split(' ')[-1]

        if args.emit_MCU:
            self.emit_MCU.connect_Serial(serial.Serial(ports[num].device,self.bb_config[name]['baud']))
            if not self.emit_MCU.connection_status():
                failed =True

        elif args.record_MCU:
            pass
        elif args.left_pinna:
            pass
        elif args.right_pinna:
            pass
        elif args.gps:
            pass
        
        if failed:
            self.poutput(f"Failed to connect to {ports[num].device}!")
            return
        else:
            self.poutput(f"Success connecting to {ports[num].device}!")
        
        user_input = self.read_input("Update YAML? it fucks your file up.. y/n: ")
        while True:
            if user_input.lower() == 'y':
    
                self.bb_config[name]['port'] = ports[num].device
                self.bb_config[name]['serial_num'] = ports[num].serial_number
                with open('bb_conf.yaml', 'w') as f:
                    yaml.dump(self.bb_config,f)
                return
            elif user_input.lower() == 'n':
                return
            user_input =self.read_input("y/n: ")
                
    
    def do_status(self,args)->None:
        """Generate workup on microcontroller status's
        """
        self.poutput(f"\nBattery:\t\tNA, \t\t\t\t\t  {t_colors.FAIL}FAIL {t_colors.ENDC}")
        self.poutput(f"Body Temp:\t\tNA, \t\t\t\t\t  {t_colors.FAIL}FAIL {t_colors.ENDC}")
        
        baud = self.bb_config['emit_MCU']['baud']
        sn = self.bb_config['emit_MCU']['serial_num']
        port = get_serial_port_from_serial_number(sn)
        try:
            if not self.emit_MCU.connection_status():
                self.emit_MCU.connect_Serial(serial.Serial(port,baudrate=baud))
                
            self.poutput(f"Emit MCU-UART: \t\tport:{port} \t\t  {t_colors.OKGREEN}OK {t_colors.ENDC}")
        except:
            self.poutput(f"Emit MCU-UART: \t\tport:{port} \t\t  {t_colors.FAIL}FAIL {t_colors.ENDC}")


        baud = self.bb_config['record_MCU']['baud']
        sn = self.bb_config['record_MCU']['serial_num']
        port = get_serial_port_from_serial_number(sn)
        try:
            if not self.record_MCU.connection_status():
                self.record_MCU.connect_Serial(serial.Serial(port,baudrate=baud))
                
            self.poutput(f"Record MCU-UART:\tport:{port} \t  {t_colors.OKGREEN}OK {t_colors.ENDC}")
        except:
            self.poutput(f"Record MCU-UART:\tport:{port} \t  {t_colors.FAIL}FAIL {t_colors.ENDC}")
     
     
        port = self.bb_config['gps_MCU']['port']
        try:
            if not self.gps_MCU.connection_status():
                self.gps_MCU.connect_Serial(serial.Serial(port))
            if not self.gps_MCU.connection_status():
                raise
                
            self.poutput(f"GPS MCU-UART:\t\tport:{port} \t\t  {t_colors.OKGREEN}OK {t_colors.ENDC}")
        except:
            self.poutput(f"GPS MCU-UART:\t\tport:{port} \t\t  {t_colors.FAIL}FAIL {t_colors.ENDC}")
        
        
        bus = self.bb_config['left_pinnae_MCU']['bus']
        ss = self.bb_config['left_pinnae_MCU']['ss']
        try:
            if self.L_pinna_MCU.com_type == pinnae.COM_TYPE.NONE:
                self.L_pinna_MCU.config_spi(bus,ss)
            
            if not self.L_pinna_MCU.get_ack():
                raise
            self.poutput(f"Left Pinna MCU-SPI:\tbus:{bus} ss:{ss}, \t\t\t\t {t_colors.OKGREEN} OK {t_colors.ENDC} ")
        except:
            self.poutput(f"Left Pinna MCU-SPI:\tbus:{bus} ss:{ss}, \t\t\t\t {t_colors.FAIL} FAIL {t_colors.ENDC} ")

        bus = self.bb_config['right_pinnae_MCU']['bus']
        ss = self.bb_config['right_pinnae_MCU']['ss']
        try:
            if self.R_pinna_MCU.com_type == pinnae.COM_TYPE.NONE:
                self.R_pinna_MCU.config_spi(bus,ss)
            
            if not self.R_pinna_MCU.get_ack():
                raise
            self.poutput(f"Right Pinna MCU-SPI:\tbus:{bus} ss:{ss}, \t\t\t\t {t_colors.OKGREEN} OK {t_colors.ENDC} ")
        except:
            self.poutput(f"Right Pinna MCU-SPI:\tbus:{bus} ss:{ss}, \t\t\t\t {t_colors.FAIL} FAIL {t_colors.ENDC} ")
            
        
        self.poutput(f"{t_colors.FAIL}\t LIMITED CAPABILITIES{t_colors.ENDC}")
        
        
        

    
    listen_parser = Cmd2ArgumentParser()
    listen_parser.add_argument('listen_time_ms',type=int,help="Time to listen for in ms")
    listen_parser.add_argument('-p','--plot',action='store_true',help="Plot the results")
    listen_parser.add_argument('-fft','--fft',action='store_true',help="Plot the fft")
    @with_argparser(listen_parser)
    def do_listen(self,args):
        """Listen for echos 

        Args:
            args (_type_): _description_
        """
        
        self.emit_MCU.write_cmd(bb_emitter.ECHO_SERIAL_CMD.EMIT_CHIRP)
        _,L,R = self.record_MCU.listen(args.listen_time_ms)
        
        if args.plot and args.fft:
            Fs = self.record_MCU.sample_freq
            T = 1/Fs
            x_vals = np.linspace(0,len(L)/Fs,num=len(L))
            plt.figure()
            plt.subplot(2,2,1)
            plt.plot(x_vals,L,'o-',markersize=0.2)
            plt.xlabel("Time")
            plt.subplot(2,2,2)
            plt.plot(x_vals,R,markersize=0.2)
            plt.xlabel("Time")   


            [X,freqs] = gen_fft(L)
            plt.subplot(2,2,3)
            plt.plot(freqs, np.abs(X),linewidth=1)
            plt.title('FFT')
            plt.xlabel('Frequency [Hz]')
            plt.ylabel('Magnitude')
            plt.xlim(0, Fs/2 )  # Display only positive frequencies
   
    
            [X,freqs] = gen_fft(R)
            plt.subplot(2,2,4)
            plt.plot(freqs, np.abs(X),linewidth=1)
            plt.title('FFT')
            plt.xlabel('Frequency [Hz]')
            plt.ylabel('Magnitude')
            plt.xlim(0, Fs/2 )  # Display only positive frequencies
            plt.tight_layout()
            plt.show()    
            plt.close()   
        elif args.plot:
            Fs = self.record_MCU.sample_freq
            T = 1/Fs
            x_vals = np.linspace(0,len(L)/Fs,num=len(L))
            plt.figure()
            plt.subplot(1,2,1)
            plt.plot(x_vals,L)
            plt.xlabel("Time")
            plt.subplot(1,2,2)
            plt.plot(x_vals,R)
            plt.xlabel("Time")   
            plt.show()
            plt.close()
            
        elif args.fft:
            # do fft
            plt.figure()

            [X,freqs]= gen_fft(L)
            plt.subplot(1,2,1)
            plt.plot(freqs, np.abs(X),'-',linewidth=1)
            plt.title('FFT')
            plt.xlabel('Frequency [Hz]')
            plt.ylabel('Magnitude')
            plt.xlim(0, Fs/2 )  # Display only positive frequencies
   

            [X,freqs]= gen_fft(R)
            plt.subplot(1,2,2)
            plt.plot(freqs, np.abs(X),'-',linewidth=1)
            plt.title('FFT')
            plt.xlabel('Frequency [Hz]')
            plt.ylabel('Magnitude')
            plt.xlim(0, Fs/2 )  # Display only positive frequencies
            # plt.tight_layout()
            plt.show()    
            plt.close()
            

    upload_sine_parser = Cmd2ArgumentParser()
    upload_sine_parser.add_argument('-f','--freq',help='frequency to gen, > 1Hz only, use xk',required=True,type=str)
    upload_sine_parser.add_argument('-t','--time',help='Time in ms to chirp, max is 60ms',type=int,default=30)
    upload_sine_parser.add_argument('-p','--plot',help='Preview',action='store_true')
    upload_sine_parser.add_argument('-fft','--fft',help='fft plot',action='store_true')
    @with_argparser(upload_sine_parser)
    def do_upload_sine(self,args):
        if args.time < 0 or args.time > 60:
            self.perror("-t must be [0,60]!")
            return
        freq = convert_khz(args.freq)
        
        [s,t] = self.emit_MCU.gen_sine(args.time,freq)
        
        if args.plot and args.fft:
            plt.figure()
            plt.subplot(1,2,1)
            plt.plot(t,s,'o-',linewidth=0.4,markersize=0.4)

            [X,freqs] = gen_fft(s)
            plt.subplot(1,2,2)
            plt.plot(freqs,np.abs(X),'-',linewidth = 1)
            plt.title('FFT')
            plt.xlabel('Frequency [Hz]')
            plt.ylabel('Magnitude')
            plt.xlim(0, 1e6/2 )  # Display only positive frequencies
            plt.show()
            plt.close()
        elif args.plot:
            plt.figure()
            plt.plot(t,s,'o-',linewidth=0.4,markersize=0.4)
            plt.show()
            plt.close()
        elif args.fft:
            plt.figure()
            [X,freqs] = gen_fft(s)
            plt.plot(freqs,np.abs(X),'-',linewidth = 1)
            plt.title('FFT')
            plt.xlabel('Frequency [Hz]')
            plt.ylabel('Magnitude')
            plt.xlim(0, 1e6/2 )  # Display only positive frequencies
            plt.show()
            plt.close()            
        
        val = input(f"Sure you want to upload? y/n: ")
        
        while True:
            if val.lower() == 'y':
                break
            elif val.lower() == 'n':
                return
            val = input(f"y/n: ")
            
        self.emit_MCU.upload_chirp(data=s)


    upload_chirp_parser = Cmd2ArgumentParser()
    upload_chirp_parser.add_argument('-f0','--freq0',help='start freq',required=True,type=str)
    upload_chirp_parser.add_argument('-f1','--freq1',help='end freq',required=True,type=str)
    upload_chirp_parser.add_argument('-t','--time',help='Time in ms to chirp, max is 60ms',type=int,default=30)
    upload_chirp_parser.add_argument('-m','--method',help='linear, quadratic..',type=str,default='linear')
    upload_chirp_parser.add_argument('-p','--plot',help='Preview',action='store_true')
    upload_chirp_parser.add_argument('-fft','--fft',help='Preview',action='store_true')
    @with_argparser(upload_chirp_parser)
    def do_upload_chirp(self,args):
        if args.time < 0 or args.time > 60:
            self.perror("-t must be [0,60]!")
            return

        freq0 = convert_khz(args.freq0)
        freq1 = convert_khz(args.freq1)

        [s,t] = self.emit_MCU.gen_chirp(freq0,freq1,args.time,args.method)

        if args.plot and args.fft:
            plt.figure()
            plt.subplot(1,2,1)
            plt.plot(t,s,'o-',linewidth=0.4,markersize=0.4)

            [X,freqs] = gen_fft(s)
            plt.subplot(1,2,2)
            plt.plot(freqs,np.abs(X),'-',linewidth = 1)
            plt.title('FFT')
            plt.xlabel('Frequency [Hz]')
            plt.ylabel('Magnitude')
            plt.xlim(0, 1e6/2 )  # Display only positive frequencies
            plt.show()
            plt.close()
        elif args.plot:
            plt.figure()
            plt.plot(t,s,'o-',linewidth=0.4,markersize=0.4)
            plt.show()
            plt.close()
        elif args.fft:
            plt.figure()
            [X,freqs] = gen_fft(s)
            plt.plot(freqs,np.abs(X),'-',linewidth = 1)
            plt.title('FFT')
            plt.xlabel('Frequency [Hz]')
            plt.ylabel('Magnitude')
            plt.xlim(0, 1e6/2 )  # Display only positive frequencies
            plt.show()
            plt.close()     

        val = input(f"Sure you want to upload? y/n: ")

        while True:
            if val.lower() == 'y':
                break
            elif val.lower() == 'n':
                return
            val = input(f"y/n: ")

        self.emit_MCU.upload_chirp(data=s)
    

    def do_chirp(self,args):
        # self.emit_MCU.chirp()
        self.emit_MCU.write_cmd(bb_emitter.ECHO_SERIAL_CMD.EMIT_CHIRP)
            
if __name__ == '__main__':
    bb = bb_repl()
    sys.exit(bb.cmdloop())

