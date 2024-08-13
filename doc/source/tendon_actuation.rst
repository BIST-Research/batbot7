Tendon Actuation
================

The Tendon Actuation application is responsible for sending motor commands to the motor controls
(running on an Adafruit Grand Central). 
Currently the only way to do this is through either ``pinnae.py`` or ``bb_gui.py`` programs,
which allow you to set individual motor angles for each motor.
However ``bb_gui.py`` is preferable as it allows for switching between serial communication and SPI
and can be used for development without a Raspberry

BB GUI
######

Clone this repository and navigate to the directory where you cloned it.