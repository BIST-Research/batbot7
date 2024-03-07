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
    def check_arg_index_type(arg):
        error_msg = "Invalid motor index, must be 1-7 or 'all'"
        try:
            value = int(arg)
            if 1<= value <= 7:
                return value
            else:
                raise argparse.ArgumentTypeError(error_msg)
        except ValueError:
            if arg.lower() == 'all':
                return arg.lower()
            else:
                raise argparse.ArgumentTypeError(error_msg)
            
    def check_arg_arg_type(arg):
        error_msg = "Invalid angle, must be int16 number, 'max' or 'min'"
        try:
            value = int(arg)
            if INT16_MIN <= value <= INT16_MAX:
                return value
            else:
                raise argparse.ArgumentTypeError(error_msg)
        except ValueError:
            if arg.lower() == 'min' or 'max' or 'zero':
                return arg.lower()
            else:
                raise argparse.ArgumentTypeError(error_msg)
        
    # pinnae control
    pinna_parser = Cmd2ArgumentParser()
    pinna_parser.add_argument('index', type=check_arg_index_type, help='Use all or value 1-7 to control motor')
    pinna_parser.add_argument('arg',type=check_arg_arg_type,
                               help='arg={angle,zero}. angle: use int16 value, max, min. To set zero: zero')
    @with_argparser(pinna_parser)
    def do_pinna(self,args)->None:
        index = args.index
        arg = args.arg
        self.poutput(f"\tSetting motor {index} to {arg}")
        
        if index == 'all':
            if arg == 'max':
                self.pinnae.set_motors_to_max()
            elif arg == 'min':
                self.pinnae.set_motors_to_min()
            elif arg == 'zero':
                self.pinnae.set_all_new_zero_position()
            else:
                angles = [int(arg)]*7
                self.pinnae.set_motor_angles(angles)
                
        else:
            if arg == 'max':
                self.pinnae.set_motor_to_max(index)
            elif arg == 'min':
                self.pinnae.set_motor_to_min(index)
            elif arg =='zero':
                self.pinnae.set_new_zero_position(index)
            else:
                self.pinnae.set_motor_angle(index-1,int(arg))
                
        
            
if __name__ == '__main__':
    bb = bb_repl()
    sys.exit(bb.cmdloop())

