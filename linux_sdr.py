#!/usr/bin/env python3

### Linux SDR
# Interfaces with the created radio peripheral IP core to set the simulated ADC frequency and the tuner frequency
# Generated samples are played over the speaker and transmitted over a UDP connection to a specified IP address and UDP port

### UDP Frame format
# Bytes 0-1: 16-bit unsigned counter, increments by one in each transmitted UDP frame
# Bytes 2-1025: 512 Interleaved 16-bit signed IQ, little endian, 48 kHz sample rate

import argparse
import os
import subprocess
import mmap
import struct
import math


class LinuxSDR():
    
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
    radio_ctrl_base = mmap.mmap(file, 4096, offset=radio_periph_base_addr)

    # UDP
    udp_enable = 1
    
    # Mute status
    mute = 0

    # Stop thread flag
    stop_thread = 0

    def __init__(self, udp_ip="127.0.0.1", udp_port=25344, adc_freq=0, tuner_freq=0):
        self.udp_ip = udp_ip
        self.udp_port = udp_port
        self.udp_sender = subprocess.Popen(['./fifo_reader', udp_ip, str(udp_port)])
        self.adc_freq = adc_freq
        self.tuner_freq = tuner_freq

        self.set_ctrl_reg(self.adc_offset, self.freq_to_inc(self.adc_freq))
        self.set_ctrl_reg(self.tuner_offset, self.freq_to_inc(self.tuner_freq))
       

    def set_ctrl_reg(self, offset, val):
        '''
        Sets the value of the specified radio control register

        Parameters:
            offset (hex): the desired register memory offset value, from {adc_offset, tuner_offset, ctrl_offset}
            val (int): the value to write to the specified register
        Returns:
            None  
        '''
        self.radio_ctrl_base.seek(offset)
        self.radio_ctrl_base.write(struct.pack('i', int(val)))

    
    def get_ctrl_reg(self, offset):
        '''
        Returns the value of the specified 32-bit radio control register

        Parameters:
            offset (hex): the specified register memory offset value, from {adc_offset, tuner_offset, ctrl_offset, timer_offset}

        Returns:
            val (int): the value from the specified register
        '''
        self.radio_ctrl_base.seek(offset)
        val = int.from_bytes(self.radio_ctrl_base.read(4), 'little')
        return val
    

    def set_freq_reg(self, offset, freq):
        '''
        Updates the value in the given radio control frequency register

        Parameters:
            offset (hex): the specified register memory offset value, from {adc_offset, tuner_offset}
            freq (int): the new frequency value
        
        Returns:
            None
            
        '''
        self.set_ctrl_reg(offset, self.freq_to_inc(freq))
        if (offset == self.adc_offset):
            self.adc_freq = freq
        elif (offset == self.tuner_offset):
            self.tuner_freq = freq
        self.print_freq_update(freq)


    def toggle_mute(self):
        '''
        Toggles the mute bit in the radio control register
        '''
        self.mute ^= 1
        self.set_ctrl_reg(self.ctrl_offset, self.mute)
        if (self.mute):
            print('    Muted')
        else:
            print('    Unmuted')


    def toggle_udp(self):
        '''
        Toggles the UDP enable
        '''
        self.udp_enable ^= 1
        if (self.udp_enable):
            print('    UDP streaming enabled')
            self.send_packets(self.udp_ip, self.udp_port)
        else:
            print('    UDP streaming disabled')
            self.udp_sender.kill()


    def send_packets(self, udp_ip, udp_port):
        '''
        Runs the C program to read from the radio FIFO as a subprocess

        Parameters:
            udp_ip (str): the destination UDP IP address
            udp_port (int): the destination UDP port
            
        Returns:
            None
        '''
        self.udp_ip = udp_ip
        self.udp_port = udp_port
        try:
            self.udp_sender.kill()
        except Exception:
            pass
        self.udp_sender = subprocess.Popen(['./fifo_reader', self.udp_ip, str(self.udp_port)])
        

    def freq_to_inc(self, freq):
        '''
        Converts a desired frequency to a phase increment value for the DDS

            Parameters:
                freq (int): the input frequency value to convert

            Returns:
                phase_inc (int): the phase increment value
        '''
        phase_inc = math.floor((freq << self.PHASE_RESOLUTION_BITS) / self.SAMP_FREQ)
        return phase_inc


    def print_instructions(self):
        '''
        Prints the instructions to the user
        '''
        print("\nEnter 'f' or 'frequency' to enter an ADC frequency")
        print("Enter 't' or 'tune' to enter a tuning frequency")
        print("Enter 'u'/'U' to increase ADC frequency by 100/1000 Hz")
        print("Enter 'd'/'D' to decrease ADC frequency by 100/1000 Hz")
        print("Enter 's' or 'stream' to toggle the UDP packet streaming")
        print("Enter 'i' or 'IP' to update the destination IP address")
        print("Enter 'p' or 'port' to update the destination UDP port")
        print("Enter 'm' or 'mute' to toggle the speaker output")
        print("Enter 'h' or 'help' to repeat these instructions")
        print("Enter 'e' or 'exit' to terminate the program\n")


    def print_freq_update(self, freq):
        '''
        Prints the ADC or tuner frequency change to the user

        Parameters:
            freq (int): the new frequency
        '''
        print(f'    Frequency: {freq}')
        print(f'    Phase Increment: {self.freq_to_inc(freq)}')


def main(udp_ip, udp_port, adc_freq, tuner_freq):
    # Create SDR object
    sdr = LinuxSDR(udp_ip=udp_ip, udp_port=udp_port, adc_freq=adc_freq, tuner_freq=tuner_freq)
    
    print('\n------------------------------------')
    print('Linux SDR with Ethernet - Zach Hicks')
    print('------------------------------------\n')
    print(f'Initially configured to transmit UDP packets to {sdr.udp_ip}:{str(sdr.udp_port)}')
    sdr.print_instructions()

    # Control loop
    while(1):
        command = input("Enter a command: ")
        print('')
        if (command == 'f' or command == 'frequency'):
            adc_freq = int(input('Enter an ADC frequency: '))
            sdr.set_freq_reg(sdr.adc_offset, adc_freq)
        elif (command == 't' or command == 'tune'):
            tuner_freq = int(input('Enter a tuner frequency: '))
            sdr.set_freq_reg(sdr.tuner_offset, tuner_freq)
        elif (command == 'u'):
            adc_freq = sdr.adc_freq + 100
            sdr.set_freq_reg(sdr.adc_offset, adc_freq)
        elif (command == 'U'):
            adc_freq = sdr.adc_freq + 1000
            sdr.set_freq_reg(sdr.adc_offset, adc_freq)
        elif (command == 'd'):
            if (sdr.adc_freq >= 100):
                adc_freq = sdr.adc_freq - 100
                sdr.set_freq_reg(sdr.adc_offset, adc_freq)
            else:
                print('Frequency cannot be decreased any further!')
        elif (command == 'D'):
            if (sdr.adc_freq >= 1000):
                adc_freq = sdr.adc_freq - 1000
                sdr.set_freq_reg(sdr.adc_offset, adc_freq)
            else:
                print('Frequency cannot be decreased any further!')
        elif (command == 'm' or command == 'mute'):
            sdr.toggle_mute()
        elif (command == 's' or command == 'stream'):
            sdr.toggle_udp()
        elif (command == 'i' or command == 'IP'):
            sdr.udp_ip = input('Enter a new destination IP address: ')
            sdr.send_packets(sdr.udp_ip, sdr.udp_port)
        elif (command == 'p' or command == 'port'):
            sdr.udp_port = int(input('Enter a new destination UDP port: '))
            sdr.send_packets(sdr.udp_ip, sdr.udp_port)
        elif (command == 'h' or command == 'help'):
            sdr.print_instructions()
        elif (command == 'e' or command == 'exit'):
            sdr.set_ctrl_reg(sdr.adc_offset, 0)
            sdr.set_ctrl_reg(sdr.tuner_offset, 0)
            sdr.udp_sender.kill()
            print('Terminated UDP sender...')
            print('Exiting...')
            print('')
            quit()
        print('')



if __name__ == '__main__':
    description = "Linux SDR with Ethernet - Loads the FPGA images and starts an interactive session with the user to control the radio and transmit the baseband signal samples over a UDP connection"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-d', '--dest_ip_addr', nargs='?', help='Destination IP address', default='127.0.0.1')
    parser.add_argument('-p', '--port', nargs='?', help='Destination UDP port', default=25344)
    parser.add_argument('-f', '--freq', nargs='?', help='Simulated ADC frequency (Hz)', default=0)
    parser.add_argument('-t', '--tuner_freq', nargs='?', help='Tuner frequency (Hz)', default=0)
    args = parser.parse_args()

    # Load FPGA images
    codec_config_cmd = 'fpgautil -b config_codec.bit.bin'
    radio_config_cmd = 'fpgautil -b design_1_wrapper.bit.bin'
    print('')
    print("Loading codec_config.bit.bin ...")
    print('')
    subprocess.run(codec_config_cmd, shell=True)
    print('')
    print("Loading design_1_wrapper.bit.bin ...")
    print('')
    subprocess.run(radio_config_cmd, shell=True)

    main(args.dest_ip_addr, int(args.port), int(args.freq), int(args.tuner_freq))