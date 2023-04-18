#!/usr/bin/env python3

### Milestone Option 1: UDP Packet Sending
# Write a program to send a fixed number of UDP packets in the format described in the lab appendix. 
# The data payload can be completely fake, just not all zeros. 
# The packet should have the right length and port, and should go to a known, but configurable destination. 
# Ways to do this would be a command-line parameter, config file, environment variables..etc.
# Turn In: an executable program which the instructor can run on the Zybo. 
# A call to it (ex) : “udpsender 192.168.1.23 10” will send 10 packets in the lab format to IP address 192.168.1.23. 
# Again, how your program gets the configuration parameters is up to you – just make sure you provide instructions to me on how to run it and change those parameters.

### Frame format
# Bytes 0-1: 16-bit unsigned counter, increments by one in each transmitted UDP frame
# Bytes 2-1025: 512 Interleaved 16-bit signed IQ, little endian, 48 kHz sample rate

import socket
import argparse
import subprocess

adc_addr = 0x43c00000
tuner_addr = 0x43c00004
ctrl_addr = 0x43c00008
timer_addr = 0x43c0000c


def set_reg(reg, freq):
    command = ['devmem', hex(reg), 'w', str(freq)]
    set_val = subprocess.run(command, capture_output=True)

# struct.pack ? treat as int32
def get_reg(reg):
    command = ['devmem', hex(reg), 'w']
    read_val = subprocess.run(command, capture_output=True).stdout[0:-1]
    return read_val


def main(udp_ip, num_packets):
    udp_port = 25344
    
    payload_seq_num = range(0, num_packets)
    payload_msg = range(0, 512)

    print(f"Sending {num_packets} UDP packets to destination {udp_ip}:{udp_port} ...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for i in range(0, num_packets):
        payload_bytes = payload_seq_num[i].to_bytes(2, 'little')
        for val in payload_msg:
            payload_bytes += val.to_bytes(2, "little")
        sock.sendto(payload_bytes, (udp_ip, udp_port))
    
if __name__ == '__main__':
    description = "Transmits a fixed number of UDP packets using the Module 7 lab packet format"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-d', '--ip', help='Destination IP address')
    parser.add_argument('-n', '--number', nargs='?', help='Number of UDP packets to send', default=10)
    args = parser.parse_args()

    main(args.ip, int(args.number))