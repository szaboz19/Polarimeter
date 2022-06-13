# Polarimeter
simple program with gui to measure photodiode current and rotate a polarizator


This is a unique python code with gui (pyQt5) to be able to use a homemade polarizer-rotator and a photodiode amplifier syncronized. I'm using Spyder python environment, which is coming with pyQT5, but pyqt5-tools package is maybe needed to get the Qt-Designer application.  

Rotator
The rotator is based on this work:
https://opg.optica.org/ao/fulltext.cfm?uri=ao-60-13-3764&id=450413
This is a cheap, homemade rotator with stepper motor. The 
3D files and arduino code available on thingiverse: https://www.thingiverse.com/thing:4401441
Many thanks for the authors! - Daniel P. G. Nilsson, Tobias Dahlberg, and Magnus Andersson

I've modified few things:
1. The rotation mount from Thorlabs is still expensive, so I made a 3D printed version.
2. I had a different stepper motor driver, modified the arduino code regarding the difference
3. I've added few more serial commands to the arduino code 

--------------------------------------------------------


Photodiode amplifier
Basic photodiode amplifier made by an other researcher collegue many years ago. I have the manual with the the few serial commands.
It has 2 channels: A, B
Mode: Current or Voltage
Range: 5 different (5 - 200uA, 4 - 20uA, 3 - 2uA, 2 - 200nA, 1 - 20nA and 0 means AUTO-range)
Number of measurements to average: 1..100 (single measurement takes ~1/16 seconds)
There is a continous mode and a "take n measurement" option



Why can be still usefull for somebody?
It uses 2 different serial devices, the incoming serial data is handled in another thread in the background and it is plotting the result in live. There is a live data mode for adjusting the optical system, angle... and a measurement mode to measure photodiode current syncronized with the angle sweep from "start andgle" to "stop angle" by "step angle". 





TODO:
there is a lot of unhandled scenario: (but it's OK for me)
1. there is no checking after the connected devices. The first send message should be examine after the correct name and version.
2. some buttons and edit boxes should be inactive when they could cause conflicts
3. fitting cos^2 function to the result ?
4. cosmetics on gui




HOW TO USE?
You need pyQT5, pyserial, matplotlib
(pip install ....)
run rotator_main.py



HOW TO MODIFY?
1. Open rotator_gui.ui in QT's Designer application. Modify, save.

2. Run "pyuic5 -x rotator_gui.ui -o rotator_gui.py" in command line to generate the py file of the gui.

3. Modify rotator_main.py, run from Spyder or from command line...

4. to generate EXE - you need to install "pyinstaller" (pip install pyinstaller) and run "pyinstaller rotator_main.py"
    ("import PyQT5.sip" line is necessary in the python code to succesfully generate the EXE file with all the dependancies)
    remark: I had to install python separately as well, because python coming from Spyder has some issues: Windows 10-11 can't see even after I've added to the       "environmental variables PATH"


