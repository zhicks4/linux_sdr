# Linux SDR

## EN 525.742 Lab Assignment: Linux SDR with Ethernet

Begin with steps 1 and 2 to generate a new FPGA .bit file, otherwise skip to step 3 to use the prebuilt version in this repository

1) Run `make_project.bat` (windows) or `make_project.sh` (linux) to create the vivado project and generate a bitfile

2) Run `make_bitbin.bat` to convert `design_1_wrapper.bit` bitfile to `.bit.bin` format

3) Copy the `config_codec.bit.bin`, `design_1_wrapper.bit.bin`, `linux_sdr.py`, and `fifo_reader.c` files into the same directory on the Zybo

4) On the Zybo, run `python3 linux_sdr.py` - note that the python script will handle calling `gcc` to build the C executable and `fpgautil` to load the two FPGA images

Usage for `linux_sdr.py` is as follows:

```python
python3 linux_sdr.py -d [DESTINATION_IP] -p [DESTINATION_UDP_PORT] -f [ADC_FREQUENCY] -t [TUNER_FREQUENCY]
```

Documentation for the program can also be displayed by the command `python3 linux_sdr.py -h`

Once the program is running, the commands to interact with the radio will be displayed in the terminal:

```
Enter 'f' or 'frequency' to enter an ADC frequency
Enter 't' or 'tune' to enter a tuning frequency   
Enter 'u'/'U' to increase ADC frequency by 100/1000 Hz  
Enter 'd'/'D' to decrease ADC frequency by 100/1000 Hz  
Enter 's' or 'stream' to toggle the UDP packet streaming
Enter 'i' or 'IP' to update the destination IP address  
Enter 'p' or 'port' to update the destination UDP port
Enter 'm' or 'mute' to toggle the speaker output      
Enter 'h' or 'help' to repeat these instructions      
Enter 'e' or 'exit' to terminate the program
```

The baseband data from the UDP packets can be plotted using the `collect_data_comples.m` MATLAB script by configuring the radio to stream UDP packets to your host computer's IP address and changing the UDP port to match the radio configuration - note that this MATLAB script was modified to reverse the order of the interleaved I and Q samples from the provided MATLAB script
