# batbot7_sonar

Connections : 

Connect the underside wires of x1, the first three are +12v, connect only the 2nd and third pin(12v from a power supply), the 4th pin should be connected to a 5v(on supply, for powering arduino, unless the arduinio is plugged into your laptop), and the last two are grounded  

For x5, the right 4 pins are voltage, but the two closer to middle are low-noise pins, connect a low noise pin to the positive end of each mic 

Far left two are Vb, not using those, ground to the 3 and 4th pins, connect a ground pin to the negative end of each mic 

Add an amp to the top 

Add the arduino to the jpL jp6 

Add jumpers to jp3 and jp4 as necessary(copy old test)git 

Connect microphone(s) to jp7 and/or jp8, yellow wire connected to arduino side 

Transducers positive side are the inside long end, negative side(gnd) is the outside long end 

 

Utility 

Knobs are for amp, R1 is big changes, r2 is small changes 

 

 

Testing: 

upload code onto arduino  

Download the run_chirp script from fieldbot repository, then run the run_chirp python script by having python in your CLI, then use your command line to go to the python script directory, then write the command  

python run_chirp.py asd 0 30000 120000 

 

Below is the descriptors of the inputs 

python run_chirp.py [output_name] [time_offset] [frequency_low] [frequency_high] 

 

A gui of the chirp receive should pop up 