# radio_periph_lab

Note : if you are building in windows and vivado is not installed in c:\Xilinx\Vivado\2021.2, you will have to change one thing
I included the settings64.bat file in the make_project.bat just to save a step.  Change that to your Install directory

run make_project.bat (windows) or make_project.sh (linux) to build the project all the way through SD card creation.  You can of course
edit in the GUI and debug in Vitis GUI afterwards as well.  The Vivado project is in "vivado" and the vitis workspace will be in "vitis"

Only downside of this (haven't fixed it yet) the C code for the processor is copied into the Vitis workspace, not linked from the original
version controlled SRC directory.  So, if you change it, you have to copy it back there.  There is a solution to this of course, but haven't 
done it yet

The base distributed project for the radio peripheral laboratory
