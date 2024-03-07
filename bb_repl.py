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
import pinnae
import bb_gps2


class batbot(Cmd):
    """BatBot 7's repl interface class
    """
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
    
    
    def do_generate_chirpd(self,args)->None:
        pass
            
if __name__ == '__main__':
    bb = batbot()
    sys.exit(bb.cmdloop())

