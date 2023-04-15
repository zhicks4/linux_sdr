#!/usr/bin/env python3

### Linux SDR
# Interfaces with the created radio peripheral IP core to set the simulated ADC frequency and the tuner frequency
# Generated samples are played over the speaker and transmitted over a UDP connection to a specified IP address and UDP port

### UDP Frame format
# Bytes 0-1: 16-bit unsigned counter, increments by one in each transmitted UDP frame
# Bytes 2-1025: 512 Interleaved 16-bit signed IQ, little endian, 48 kHz sample rate

import socket
import argparse
import os
import subprocess
import mmap
import struct
import math

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
    '''
    Toggles the mute bit in the radio control register
    '''
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


def send_packet(sock, payload, udp_ip, udp_port):
    '''
    Transmits a UDP datagram of radio output samples to the provided UDP port

    Parameters:
        sock (socket): the socket object
        payload (bytes): the data payload of radio samples
        udp_ip (str): the destination IP address
        udp_port (int): the destination port

    Returns:
        None
    '''
    sock.sendto(payload, (udp_ip, udp_port))


def print_instructions():
    '''
    Prints the instructions to the user
    '''
    print("\nEnter 'f' or 'frequency' to enter an ADC frequency")
    print("Enter 't' or 'tune' to enter a tuning frequency")
    print("Enter 'u'/'U' to increase ADC frequency by 100/1000 Hz")
    print("Enter 'd'/'D' to decrease ADC frequency by 100/1000 Hz")
    print("Enter 'i' or 'IP' to update the destination IP address")
    print("Enter 'p' or 'port' to update the destination UDP port")
    print("Enter 'm' or 'mute' to toggle the speaker output")
    print("Enter 'h' or 'help' to repeat these instructions\n")


def print_freq_update(freq, phase_inc):
    '''
    Prints the ADC or tuner frequency change to the user
    '''
    print(f'    Frequency: {freq}')
    print(f'    Phase Increment: {phase_inc}')


def main(udp_ip, udp_port, adc_freq, tuner_freq):
    
    ip = udp_ip
    port = udp_port
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload_seq_num = 0
    adc_phase_inc = freq_to_inc(adc_freq)
    tuner_phase_inc = freq_to_inc(tuner_freq)

    # TODO: add multithreading for reading FIFO and creating UDP packets
    '''
    fifo_count = get_radio_reg(fifo_count_offset)
    if (fifo_count = 256):
        payload = []
        for i in range(0, 256):
            next_fifo_word = get_radio_reg(fifo_data_offset)
            payload.append(next_fifo_word)
        send_packet(sock, payload, ip, port)
    '''

    print('\nLinux SDR with Ethernet - Zach Hicks\n')
    print(f'Initially configured to transmit UDP packets to {ip}:{port}')
    print_instructions()

    # Control loop
    while(1):
        command = input("Enter a command: ")
        print('')
        if (command == 'f' or command == 'frequency'):
            adc_freq = int(input('Enter an ADC frequency: '))
            adc_phase_inc = freq_to_inc(adc_freq)
            set_radio_reg(mem_radio, adc_offset, adc_phase_inc)
            print_freq_update(adc_freq, adc_phase_inc)
        elif (command == 't' or command == 'tune'):
            tuner_freq = int(input('Enter a tuner frequency: '))
            tuner_phase_inc = freq_to_inc(tuner_freq)
            set_radio_reg(mem_radio, tuner_offset, tuner_phase_inc)
            print_freq_update(tuner_freq, tuner_phase_inc)
        elif (command == 'u'):
            adc_freq += 100
            adc_phase_inc = freq_to_inc(adc_freq)
            set_radio_reg(mem_radio, adc_offset, adc_phase_inc)
            print_freq_update(adc_freq, adc_phase_inc)
        elif (command == 'U'):
            adc_freq += 1000
            adc_phase_inc = freq_to_inc(adc_freq)
            set_radio_reg(mem_radio, adc_offset, adc_phase_inc)
            print_freq_update(adc_freq, adc_phase_inc)
        elif (command == 'd'):
            if (adc_freq >= 100):
                adc_freq -= 100
                adc_phase_inc = freq_to_inc(adc_freq)
                set_radio_reg(mem_radio, adc_offset, adc_phase_inc)
                print_freq_update(adc_freq, adc_phase_inc)
            else:
                print('Frequency cannot be decreased any further!')
        elif (command == 'D'):
            if (adc_freq >= 1000):
                adc_freq -= 1000
                adc_phase_inc = freq_to_inc(adc_freq)
                set_radio_reg(mem_radio, adc_offset, adc_phase_inc)
                print_freq_update(adc_freq, adc_phase_inc)
            else:
                print('Frequency cannot be decreased any further!')
        elif (command == 'm' or command == 'mute'):
            toggle_mute()
        elif (command == 'i' or command == 'IP'):
            ip = input('Enter a new destination IP address: ')
        elif (command == 'p' or command == 'port'):
            port = input('Enter a new destination UDP port: ')
        elif (command == 'h' or command == 'help'):
            print_instructions()
        print('')



if __name__ == '__main__':
    description = "Linux SDR with Ethernet"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-d', '--dest_ip_addr', nargs='?', help='Destination IP address', default='127.0.0.1')
    parser.add_argument('-p', '--port', nargs='?', help='Destination UDP port', default=25344)
    parser.add_argument('-f', '--freq', nargs='?', help='Simulated ADC frequency', default=0)
    parser.add_argument('-t', '--tuner_freq', nargs='?', help='Tuner frequency', default=0)
    args = parser.parse_args()

    codec_config_cmd = 'fpgautil -b config_codec.bit.bin'
    radio_config_cmd = 'fpgautil -b design_1_wrapper.bit.bin'
    subprocess.run(codec_config_cmd, shell=True)
    subprocess.run(radio_config_cmd, shell=True)

    main(args.dest_ip_addr, int(args.port), int(args.freq), int(args.tuner_freq))