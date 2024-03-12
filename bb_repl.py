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

INT16_MIN = np.iinfo(np.int16).min
INT16_MAX = np.iinfo(np.int16).max

class bcolors:
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
    
    pinnae = pinnae.PinnaeController()
    
    def __init__(self):
        
        self.prompt='(batbot)>> '
        super().__init__()
    

    def do_battery(self, _:Statement) ->None: 
        """Returns the battery status of batbot
        """
        self.poutput('11.7v')
        
    def do_temp(self, _:Statement)->None:
        """Returns the temperature of the batbot
        """
        self.poutput('73f OK')
        
    #--------------------------------------------------------------------------
    # chirp
    chirp_parser = Cmd2ArgumentParser()
    chirp_parser.add_argument('-r','--repeat', type=int,help='chirp [n] times')
    @with_argparser(chirp_parser)    
    def do_chirp(self, args)->None:
        """Tells the chirp MCU to chirp

        """
        repetitions = args.repeat or 1
        
        for _ in range(repetitions):
            self.poutput('chirp..')
    
    
    def do_generate_chirp(self,args)->None:
        pass
    
    #--------------------------------------------------------------------------
    # def check_arg_index_type(arg):
    #     error_msg = "Invalid motor index, must be 1-7 or 'all'"
    #     try:
    #         value = int(arg)
    #         if 1<= value <= 7:
    #             return value
    #         else:
    #             raise argparse.ArgumentTypeError(error_msg)
    #     except ValueError:
    #         if arg.lower() == 'all':
    #             return arg.lower()
    #         else:
    #             raise argparse.ArgumentTypeError(error_msg)
            
    # def check_arg_arg_type(arg):
    #     error_msg = "Invalid angle, must be int16 number, 'max' or 'min'"
    #     try:
    #         value = int(arg)
    #         if INT16_MIN <= value <= INT16_MAX:
    #             return value
    #         else:
    #             raise argparse.ArgumentTypeError(error_msg)
    #     except ValueError:
    #         if arg.lower() == 'min' or 'max' or 'zero':
    #             return arg.lower()
    #         else:
    #             raise argparse.ArgumentTypeError(error_msg)
        
    # pinnae control
    # pinna_parser = Cmd2ArgumentParser()
    # pinna_parser.add_argument('index', type=check_arg_index_type, help='Use all or value 1-7 to control motor')
    # pinna_parser.add_argument('arg',type=check_arg_arg_type,
    #                            help='arg={angle,zero}. angle: use int16 value, max, min. To set zero: zero')
    # @with_argparser(pinna_parser)
    # def do_pinna(self,args)->None:
    #     """Control the pinna

    #     """
    #     index = args.index
    #     arg = args.arg
    #     self.poutput(f"\tSetting motor {index} to {arg}")
        
    #     if index == 'all':
    #         if arg == 'max':
    #             self.pinnae.set_motors_to_max()
    #         elif arg == 'min':
    #             self.pinnae.set_motors_to_min()
    #         elif arg == 'zero':
    #             self.pinnae.set_all_new_zero_position()
    #         else:
    #             angles = [int(arg)]*7
    #             self.pinnae.set_motor_angles(angles)
                
    #     else:
    #         if arg == 'max':
    #             self.pinnae.set_motor_to_max(index)
    #         elif arg == 'min':
    #             self.pinnae.set_motor_to_min(index)
    #         elif arg =='zero':
    #             self.pinnae.set_new_zero_position(index)
    #         else:
                # self.pinnae.set_motor_angle(index-1,int(arg))
    pinna_parser = Cmd2ArgumentParser()
    pinna_parser.add_argument('-cf','--config',action='store_true',required=False)
    @with_argparser(pinna_parser)
    def do_pinna(self,args)->None:
        
        if args.config:
            self.poutput(f"{bcolors.OKGREEN}Configuring Serial or SPI{bcolors.ENDC}")
            using_spi = False
            self.poutput("Enter for configuration")
            
            while True:
                input = self.prompt("1: Serial \n2:SPI")
                if input == "quit":
                    return
                elif input == "1":
                    self.poutput("")
                    pass
                elif input == "2":
                    pass
            
                
    def do_config_gps(self,args)->None:
        pass
    
    def do_status(self,args)->None:
        """Generate workup on microcontroller status's
        """
        self.poutput(f"\nBattery Voltage: \t11.2V, \tstatus:  {bcolors.OKGREEN}OK {bcolors.ENDC}")
        self.poutput(f"Internal Temp: \t\t72f, \tstatus:  {bcolors.OKGREEN}OK {bcolors.ENDC}")
        self.poutput(f"Emit board-UART: {'com2'} \t\tstatus:  {bcolors.OKGREEN}OK {bcolors.ENDC}")
        self.poutput(f"Record board-SPI: bus:1 ss:1,  \tstatus:  {bcolors.OKGREEN}OK {bcolors.ENDC}")
        self.poutput(f"Left Pinna-SPI: bus:0 ss:0, \tstatus:  {bcolors.OKGREEN}OK {bcolors.ENDC} ")
        self.poutput(f"Right Pinna-SPI: bus:0 ss:1, \tstatus:  {bcolors.OKGREEN}OK {bcolors.ENDC} ")
        self.poutput(f"GPS Board-UART: {'com3'} \t\tstatus:  {bcolors.OKGREEN}OK {bcolors.ENDC}")
        self.poutput(f"{bcolors.OKBLUE}\tREADY FOR RUNS{bcolors.ENDC}")
        
    test_parser = Cmd2ArgumentParser()
    test_parser.add_argument('--gps',help="test GPS for output",action='store_true')
    test_parser.add_argument('--lp', help="test left pinna",action='store_true')
    test_parser.add_argument('--rp',help="test right pinna", action='store_true')
    test_parser.add_argument('--emit',help="test emit board",action='store_true')
    test_parser.add_argument('--record',help="test record board",action='store_true')
    @with_argparser(test_parser)
    def do_test(self,args)->None:
        """Tests a specific peripheral or all peripherals
        """
        pass
        
        
        
    run_parser = Cmd2ArgumentParser()
    @with_argparser(run_parser)
    def do_run(self,args)->None:
        pass
        
                
            
if __name__ == '__main__':
    bb = bb_repl()
    sys.exit(bb.cmdloop())

