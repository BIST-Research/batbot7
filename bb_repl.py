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
import matplotlib.mlab as mlab
import matplotlib.colors as colors
import logging
import serial.tools.list_ports
from PyQt6.QtWidgets import QApplication, QWidget
import threading
import bb_gui
import os
from scipy import signal

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
    X[0] = 0
    return[X,freqs]




def plot_spec(ax, fig, spec_tup, fbounds = (30E3, 100E3), dB_range = 40, plot_title = 'spec',use_khz=True):
    
    fmin, fmax = fbounds
    s, f, t = spec_tup
    
    lfc = (f >= fmin).argmax()
    s = 20*np.log10(s)
    f_cut = f[lfc:]
    s_cut = s[:][lfc:]

    
    max_s = np.amax(s_cut)
    s_cut = s_cut - max_s
    
    [rows_s, cols_s] = np.shape(s_cut)
    
    dB = -dB_range
    
    for col in range(cols_s):
        for row in range(rows_s):
            if s_cut[row][col] < dB:
                s_cut[row][col] = dB
                
    cf = ax.pcolormesh(t, f_cut, s_cut, cmap='jet', shading='auto')
    cbar = fig.colorbar(cf, ax=ax)
    
    ax.set_ylim(fmin, fmax)
    ax.set_ylabel('Frequency (Hz)')
    ax.set_xlabel('Time (sec)')
    ax.title.set_text(plot_title)

    cbar.ax.set_ylabel('dB')
    if use_khz:
        make_khz_ytick(ax)
 
            
def plot_time(ax, fig,Fs,plot_data,use_ms=True)->None:
    T = 1/Fs
    x_vals = np.linspace(0,len(plot_data)/Fs,num=len(plot_data))
    ax.plot(x_vals,plot_data,'o-',markersize=0.2)
    ax.title.set_text('Time')
    if use_ms:
        make_ms_xtick(ax)

    
def plot_fft(ax:plt.axes,fig:plt.figure,Fs,plot_data)->None:
    [X,freqs] = gen_fft(plot_data)
    
    ax.plot(freqs,np.abs(X),linewidth=1)
    ax.title.set_text('FFT')
    ax.set_xlabel('Frequency [Hz]')
    ax.set_ylabel('Magnitude')
    ax.set_xlim(0,Fs/2)
    make_khz_xtick(ax)

def make_khz_ytick(ax):
    # Get the current tick positions
    current_ticks = ax.get_yticks()
    # Convert tick positions to kHz and create labels
    new_tick_positions = current_ticks /1000
    new_tick_labels = ['{}kHz'.format(int(tick)) for tick in new_tick_positions]
    # Set y-axis ticks and labels
    # ax.set_yticks(current_ticks)
    ax.set_yticklabels(new_tick_labels)

def make_khz_xtick(ax):
    # Get the current tick positions
    current_ticks = ax.get_xticks()
    # Convert tick positions to kHz and create labels
    new_tick_positions = current_ticks /1000
    new_tick_labels = ['{}kHz'.format(int(tick)) for tick in new_tick_positions]
    # Set y-axis ticks and labels
    ax.set_xticks(current_ticks)
    ax.set_xticklabels(new_tick_labels)
    
def make_ms_xtick(ax):
        # Get the current tick positions
    current_ticks = ax.get_xticks()
    # Convert tick positions to kHz and create labels
    new_tick_positions = current_ticks *1000
    new_tick_labels = ['{}ms'.format(int(tick)) for tick in new_tick_positions]
    # Set y-axis ticks and labels
    ax.set_xticks(current_ticks)
    ax.set_xticklabels(new_tick_labels)

    

def process(raw, spec_settings, time_offs = 0):

    unraw_balanced = raw - np.mean(raw)
    
    pt_cut = unraw_balanced[time_offs:]
    remainder = unraw_balanced[:time_offs]
    
    Fs, NFFT, noverlap, window = spec_settings
    spec_tup = mlab.specgram(pt_cut, Fs=Fs, NFFT=NFFT, noverlap=noverlap, window=window)
    
    return spec_tup, pt_cut, remainder


            






class bb_repl(Cmd):
    """BatBot 7's repl interface class
    """
    
    def __init__(self,yaml_cfg_file:str = 'bb_conf.yaml'):
        
        self.prompt='(batbot)>> '
        self.yaml_cfg_file = yaml_cfg_file

        self.record_MCU = bb_listener.EchoRecorder()
        self.emit_MCU = bb_emitter.EchoEmitter()
        self.L_pinna_MCU = pinnae.PinnaeController(pinnae.SpiDev(0,0))
        self.R_pinna_MCU = pinnae.PinnaeController(pinnae.SpiDev(0,1))
        self.gps_MCU = bb_gps.bb_gps2()
        
        self.gui = None
        self.PinnaWidget = None
        
        super().__init__()
        
        self.phase_ears = False
        self.add_settable(Settable('phase_ears',bool,'when true pinnas move out of phase from each other',self))
        
        self._startup()
        
        

    
    def _startup(self):
        with open(self.yaml_cfg_file, "r") as f:
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


    def do_gui(self,args):
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])
        if not self.gui or self.gui is None:
            self.gui = bb_gui.BBGUI(self.emit_MCU,self.record_MCU,self.L_pinna_MCU,self.R_pinna_MCU)
        self.gui.show()
        self.app.exec()

    
    pinna_parser = Cmd2ArgumentParser()
    pinna_parser.add_argument('motor_number',type=int)
    pinna_parser.add_argument('motor_angle',type=int)
    pinna_parser.add_argument('-g','--gui',action='store_true')
    pinna_parser.add_argument('-cal','--calibrate',action='store_true')
    @with_argparser(pinna_parser)
    def do_pinna(self,args):
        if args.gui:
            self.app = QApplication.instance()
            if self.app is None:
                self.app = QApplication([])

            if self.PinnaWidget is None:
                self.PinnaWidget = pinnae.PinnaWidget(self.L_pinna_MCU, self.R_pinna_MCU)

            self.PinnaWidget.show()
            self.app.exec()
            
        if args.calibrate:
            l_lims = self.L_pinna_MCU.calibrate_and_get_motor_limits()
            r_lims = self.R_pinna_MCU.calibrate_and_get_motor_limits()
            
        self.poutput(f"{args}")
            
        
            
    
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
            if port is None:
                raise
            if not self.emit_MCU.connection_status():
                self.emit_MCU.connect_Serial(serial.Serial(port,baudrate=baud))
                
            self.poutput(f"Emit MCU-UART: \t\tport:{port} \t\t  {t_colors.OKGREEN}OK {t_colors.ENDC}")
        except:
            self.poutput(f"Emit MCU-UART: \t\tport:{port} \t\t  {t_colors.FAIL}FAIL {t_colors.ENDC}")


        baud = self.bb_config['record_MCU']['baud']
        sn = self.bb_config['record_MCU']['serial_num']
        port = get_serial_port_from_serial_number(sn)
        try:
            if port is None:
                raise
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
    listen_parser.add_argument('-spec','--spec',action='store_true',help="Plot the spec")
    listen_parser.add_argument('-of','--off',type=float,help="offset to start listening",default=0.008)
    @with_argparser(listen_parser)
    def do_listen(self,args):
        """Listen for echos 

        Args:
            args (_type_): _description_
        """
        
        tim = threading.Timer(args.off, self.emit_MCU.write_cmd, args=(bb_emitter.ECHO_SERIAL_CMD.EMIT_CHIRP,))
        tim.start()

        _,L,R = self.record_MCU.listen(args.listen_time_ms)
        
        num_axes = 0
        rows = 0
        if args.plot:
            rows +=1 
        if args.fft:
            rows +=1
        if args.spec:
            rows +=1
        
        fig,axes = plt.subplots(nrows=rows,ncols=2)
        Fs = self.record_MCU.sample_freq
        cur_row = 0
        if args.plot:
            if rows > 1:
                plot_time(axes[cur_row,0],fig,Fs,L)
                plot_time(axes[cur_row,1],fig,Fs,R)
            else:
                plot_time(axes[0],fig,Fs,L)
                plot_time(axes[1],fig,Fs,R)
            cur_row += 1
        if args.fft:
            if rows > 1:
                plot_fft(axes[cur_row,0],fig,Fs,L)
                plot_fft(axes[cur_row,1],fig,Fs,R)
            else:
                plot_fft(axes[0],fig,Fs,L)
                plot_fft(axes[1],fig,Fs,R)
            
            
            cur_row += 1
        if args.spec:
            NFFT = 512
            noverlap = 400
            spec_settings = (Fs, NFFT, noverlap, signal.windows.hann(NFFT))
            DB_range = 40
            f_plot_bounds = (30E3, 100E3)
            
            spec_tup1, pt_cut1, pt1 = process(L, spec_settings, time_offs=0)
            spec_tup2, pt_cut2, pt2 = process(R, spec_settings, time_offs=0)
            
            if rows > 1:
                plot_spec(axes[cur_row,0], fig, spec_tup1, fbounds = f_plot_bounds, dB_range = DB_range, plot_title='Left Ear')
                plot_spec(axes[cur_row,1], fig, spec_tup1, fbounds = f_plot_bounds, dB_range = DB_range, plot_title='Right Ear')
            else:
                plot_spec(axes[0], fig, spec_tup1, fbounds = f_plot_bounds, dB_range = DB_range, plot_title='Left Ear')
                plot_spec(axes[1], fig, spec_tup1, fbounds = f_plot_bounds, dB_range = DB_range, plot_title='Right Ear')
                
            
        plt.subplots_adjust(wspace=0.5,hspace=0.3)
        plt.show()
        plt.close()
        
            

    upload_sine_parser = Cmd2ArgumentParser()
    upload_sine_parser.add_argument('-f','--freq',help='frequency to gen, > 1Hz only, use xk',required=True,type=str)
    upload_sine_parser.add_argument('-t','--time',help='Time in ms to chirp, max is 60ms',type=int,default=30)
    upload_sine_parser.add_argument('-p','--plot',help='Preview',action='store_true')
    upload_sine_parser.add_argument('-fft','--fft',help='fft plot',action='store_true')
    upload_sine_parser.add_argument('-g','--gain',help='typical gain',type=int,default=512)
    @with_argparser(upload_sine_parser)
    def do_upload_sine(self,args):
        freq = convert_khz(args.freq)
        

        [s,t] = self.emit_MCU.gen_sine(args.time,freq,args.gain)
        
        if args.plot and args.fft:
            fig,ax = plt.subplots(ncols=2)
            Fs = self.record_MCU.sample_freq
            
            plot_time(ax[0],fig,Fs,s)
            plot_fft(ax[1],fig,Fs,s)
            
            plt.show()
            plt.close()
        elif args.plot:

            fig,ax = plt.subplots(ncols=1)
            Fs = self.record_MCU.sample_freq
            plot_time(ax,fig,Fs,s)
            plt.show()
            plt.close()
        elif args.fft:
            fig,ax = plt.subplots(ncols=1)
            Fs = self.record_MCU.sample_freq
            plot_fft(ax,fig,Fs,s)
            
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
    upload_chirp_parser.add_argument('-g','--gain',help='gain to boost signal for DAC',type=int,default=512)
    upload_chirp_parser.add_argument('-m','--method',help='linear, quadratic..',type=str,default='linear')
    upload_chirp_parser.add_argument('-p','--plot',help='Preview',action='store_true')
    upload_chirp_parser.add_argument('-fft','--fft',help='Preview',action='store_true')
    @with_argparser(upload_chirp_parser)
    def do_upload_chirp(self,args):
        freq0 = convert_khz(args.freq0)
        if freq0 is None:
            self.perror("-f0 should be xk")
        freq1 = convert_khz(args.freq1)
        if freq1 is None:
            self.perror("-f1 should be xk")

        [s,t] = self.emit_MCU.gen_chirp(freq0,freq1,args.time,args.method,args.gain)

        if args.plot and args.fft:
            fig,ax = plt.subplots(ncols=2)
            Fs = self.record_MCU.sample_freq
            
            plot_time(ax[0],fig,Fs,s)
            plot_fft(ax[1],fig,Fs,s)
            
            plt.show()
            plt.close()
        elif args.plot:

            fig,ax = plt.subplots(ncols=1)
            Fs = self.record_MCU.sample_freq
            plot_time(ax,fig,Fs,s)
            plt.show()
            plt.close()
        elif args.fft:
            fig,ax = plt.subplots(ncols=1)
            Fs = self.record_MCU.sample_freq
            plot_fft(ax,fig,Fs,s)
            
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

