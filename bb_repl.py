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
        exit
                
    def do_batt(self, _:Statement) ->None: 
        """Returns the battery status of batbot
        """
        self.poutput('11.7v')
        
    def do_temp(self, _:Statement)->None:
        """Returns the temperature of the batbot
        """
        self.poutput('73f OK')
        

    def do_gen_chirp(self,args)->None:
        pass
    
    config_parser = Cmd2ArgumentParser()
    config_parser.add_argument('-e','--emit_MCU',action='store_true',help="config emit board")
    config_parser.add_argument('-r','--record_MCU',action='store_true',help="config record board")
    config_parser.add_argument('-lp','--left_pinna',action='store_true',help='config left pinna')
    config_parser.add_argument('-rp','--right_pinna',action='store_true',help='config right pinna')
    config_parser.add_argument('-g','--gps',action='store_true',help='config gps com')
    @with_argparser(config_parser)
    def do_config(self,args):

        

        # Get a list of available serial ports
        ports = serial.tools.list_ports.comports()
    
        for i,port in enumerate(ports):
            self.poutput(f"{i}. {port.device}")
            
        self.poutput(f"select port")
            
                
    
    def do_status(self,args)->None:
        """Generate workup on microcontroller status's
        """
        self.poutput(f"\nBattery:\t\tNA, \t\t\t\t\t  {t_colors.FAIL}FAIL {t_colors.ENDC}")
        self.poutput(f"Body Temp:\t\tNA, \t\t\t\t\t  {t_colors.FAIL}FAIL {t_colors.ENDC}")
        
        port = self.bb_config['emit_MCU']['port']
        baud = self.bb_config['emit_MCU']['baud']
        try:
            if not self.emit_MCU.connection_status():
                self.emit_MCU.connect_Serial(serial.Serial(port,baudrate=baud))

                
            self.poutput(f"Emit MCU-UART: \t\tport:{port} \t\t  {t_colors.OKGREEN}OK {t_colors.ENDC}")
        except:
            self.poutput(f"Emit MCU-UART: \t\tport:{port} \t\t  {t_colors.FAIL}FAIL {t_colors.ENDC}")


        port = self.bb_config['record_MCU']['port']
        baud = self.bb_config['record_MCU']['baud']
        try:
            if not self.record_MCU.connection_status():
                self.record_MCU.connect_Serial(serial.Serial(port,baudrate=baud))
            # if not self.record_MCU.connection_status():
            #     raise
                
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
        # if not self.record_MCU.check_status():
        #     self.poutput(f"{t_colors.FAIL}Record MCU not responding! {t_colors.ENDC}")
        
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

            N = len(L)
            X = np.fft.fft(L)
            # Set x-axis ticks and labels in kHz
            # plt.xticks(np.arange(0, 10001, 1000), [f'{freq/1000:.0f} kHz' for freq in np.arange(0, 10001, 1000)])

            freqs = np.fft.fftfreq(N,d=T)
            plt.subplot(2,2,3)
            plt.plot(freqs, np.abs(X),linewidth=1)
            plt.title('FFT')
            plt.xlabel('Frequency [Hz]')
            plt.ylabel('Magnitude')
            plt.xlim(0, Fs/2 )  # Display only positive frequencies
   
            X = np.fft.fft(R)
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
            Fs  = self.record_MCU.sample_freq
            T = 1/Fs
            N = len(L)
            X = np.fft.fft(L)
            freqs = np.fft.fftfreq(N,d=T)
            plt.subplot(1,2,1)
            plt.plot(freqs, np.abs(X),linewidth=1)
            plt.title('FFT')
            plt.xlabel('Frequency [Hz]')
            plt.ylabel('Magnitude')
            plt.xlim(0, Fs/2 )  # Display only positive frequencies
   
            X = np.fft.fft(R)
            plt.subplot(1,2,2)
            plt.plot(freqs, np.abs(X),linewidth=1)
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
    @with_argparser(upload_sine_parser)
    def do_upload_sine(self,args):
        if args.time < 0 or args.time > 60:
            self.perror("-t must be [0,60]!")
            return
        freqstr = args.freq.lower()
        val = freqstr.split('k')
        if not val[0].isdigit():
            self.perror(f"-f {freqstr} is not valid, use xk")
            return
        
        if freqstr.endswith('k'):
            freq = int(val[0])*1e3
        else:
            freq = int(val[0])
        
        [s,t] = self.emit_MCU.gen_sine(args.time,freq)
        
        if args.plot:
            plt.figure()
            plt.plot(t,s,'o-',linewidth=0.4,markersize=0.4)
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

