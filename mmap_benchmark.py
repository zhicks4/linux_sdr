from linux_sdr import *
import subprocess

num_reads = 2048
word_length_bytes = 4
clk_freq = 125000000
clk_period = 1/clk_freq

# Load FPGA images
codec_config_cmd = 'fpgautil -b config_codec.bit.bin'
radio_config_cmd = 'fpgautil -b design_1_wrapper.bit.bin'
subprocess.run(codec_config_cmd, shell=True)
subprocess.run(radio_config_cmd, shell=True)

sdr = LinuxSDR()

start_time = sdr.get_ctrl_reg(sdr.timer_offset)
stop_time = start_time
for i in range(0, num_reads):
    stop_time = sdr.get_ctrl_reg(sdr.timer_offset)

bytes_transferred = num_reads * word_length_bytes
clks_elapsed = stop_time - start_time
time_spent = clks_elapsed * clk_period
throughput = bytes_transferred / time_spent
throughput_kBps = throughput / 1e3

print('')
print(f'Elapsed time in clocks = {clks_elapsed}')
print(f'You transferred {bytes_transferred} bytes of data in {time_spent} seconds')
print(f'Measured transfer throughput = {throughput_kBps} kBytes/s')