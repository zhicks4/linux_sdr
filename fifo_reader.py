#!/usr/bin/env python3

### Linux SDR Milestone 2 - Radio + Custom FIFO Peripheral
# Demonstrates radio FIFO by reading 480,000 samples from the FIFO

import os
import argparse
import subprocess
import mmap
import struct
import math
import time

# Define memory-mapped peripheral addresses and offsets
radio_periph_base_addr = 0x43c00000
adc_offset = 0x00
tuner_offset = 0x04
ctrl_offset = 0x08
timer_offset = 0x0c
fifo_base_addr = 0x43c10000
fifo_data_offset = 0x00
fifo_count_offset = 0x04

# Define constants
SAMP_FREQ = 125000000
PHASE_RESOLUTION_BITS = 27

# Open memory-mapped peripheral location
file = os.open('/dev/mem', os.O_RDWR, os.O_SYNC)
mem_radio = mmap.mmap(file, 4096, offset=radio_periph_base_addr)
mem_fifo = mmap.mmap(file, 4096, offset=fifo_base_addr)

# Misc global variables
mute = 0


def set_radio_reg(dev, offset, val):
    '''
    Sets the value of the specified radio control register

    Parameters:
        dev (hex): the memory mapped device to write to, from {mem_radio, mem_fifo}
        offset (hex): the desired register memory offset value, from {adc_offset, tuner_offset, ctrl_offset, timer_offset}
        val (int): the value to write to the specified register
    Returns:
        None  
    '''
    dev.seek(offset)
    dev.write(struct.pack('i', int(val)))


def get_radio_reg(dev, offset):
    '''
    Returns the value of the specified 32-bit radio control register

    Parameters:
        dev (hex): the memory mapped device to write to, from {mem_radio, mem_fifo}
        offset (hex): the specified register memory offset value, from {adc_offset, tuner_offset, ctrl_offset, timer_offset}

    Returns:
        val (int): the value from the specified register
    '''
    dev.seek(offset)
    val = int.from_bytes(dev.read(4), 'little')
    return val


def toggle_mute():
    global mute
    mute ^= 1
    set_radio_reg(mem_radio, ctrl_offset, mute)
    if (mute):
        print('    Muted')
    else:
        print('    Unmuted')


def freq_to_inc(freq):
    '''
    Converts a desired frequency to a phase increment value for the DDS

        Parameters:
            freq (int): the input frequency value to convert

        Returns:
            phase_inc (int): the phase increment value
    '''
    phase_inc = math.floor((freq << PHASE_RESOLUTION_BITS) / SAMP_FREQ)
    return phase_inc


def main(num_samples):
    
    
    adc_phase_inc = freq_to_inc(1001000)
    tuner_phase_inc = freq_to_inc(1000000)

    set_radio_reg(mem_radio, adc_offset, adc_phase_inc)
    set_radio_reg(mem_radio, tuner_offset, tuner_phase_inc)
    
    print('\nLinux SDR with Ethernet Milestone 2 - Zach Hicks\n')
    print(f'Reading {num_samples} from the radio FIFO...')
    print('')
    start = time.time()
    
    samples_read = 0

    while(samples_read <= num_samples):
        fifo_count = get_radio_reg(mem_fifo, fifo_count_offset)
        if (fifo_count > 0):
            sample = get_radio_reg(mem_fifo, fifo_data_offset)
            samples_read += 1

    end = time.time()
    print(f'Reading {num_samples} samples took {end-start} seconds')
    print('')

if __name__ == '__main__':
    description = "Linux SDR Milestone 2 - Reads samples from the radio FIFO"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-n', '--num_samps', nargs='?', help='Number of samples', default='480000')
    args = parser.parse_args()

    codec_config_cmd = 'fpgautil -b config_codec.bit.bin'
    radio_config_cmd = 'fpgautil -b design_1_wrapper.bit.bin'
    subprocess.run(codec_config_cmd, shell=True)
    subprocess.run(radio_config_cmd, shell=True)

    main(int(args.num_samps))