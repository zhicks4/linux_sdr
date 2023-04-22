% script to collect/display data from Lab 5
import java.net.*
import java.io.*
import java.nio.*

disp('Lab 9 Real-time data monitor');
disp('This program plots the time series and FFT of the data');
tic;
% set some things that might change, like the number of samples
% in one UDP frame, the port number to listen on...etc.
% This is what I use
complex_samples_per_packet = 256; 
samples_per_packet = complex_samples_per_packet*2;
port = 25344;


% for a compromise between update rate and frequency accuracy
% we'll take the simple approach of taking an FFT every 32 packets
% (8k point FFT with 250 samples/packet)

fftsize_packets = 16; 
fs = 100e6/(32*64);


bytes_per_packet = 2*samples_per_packet+2; %each packet has a 2 byte seq #

% freqs transforms the index into actual frequencies for a nice axis to
% plot against.
fftbins = linspace(1,fftsize_packets*complex_samples_per_packet,fftsize_packets*complex_samples_per_packet);
freqs = (fs/(fftsize_packets*complex_samples_per_packet))*fftbins;

% open socket and packet
% this could be improved - right now, we'll try to close the socket
% in case someone has left the socket open.
buffersize = 1000000;
try socket.close(); end
packet = DatagramPacket(zeros(1,bytes_per_packet,'int8') , bytes_per_packet);
socket = DatagramSocket(port);
socket.setSoTimeout(1000);
socket.setReuseAddress(true)
%clear buffer.  We made the buffer size large so we wouldn't ever miss
%packets.  However, we don't want old data in here, so before taking data
%we artificially clear out the buffer and then start getting data
socket.setReceiveBufferSize(1);
try 
    socket.receive(packet); % clear the buffer
catch
    disp('receive failed');
end
    

%set buffer large enough for no missed data
socket.setReceiveBufferSize(buffersize);

% prepare raw data vector
rawData = int8( zeros(bytes_per_packet) );
oldpacketct = int16(0);
while(1==1)
for i1 = 1:fftsize_packets
    try
        socket.receive(packet);
        rawData = packet.getData();
        packetct = typecast(rawData(1:2),'int16');
        if (packetct ~= (oldpacketct+1) && (packetct ~= 0))
            disp('missed packet\n');
        end
        oldpacketct = packetct;
        fftdata(((i1-1)*samples_per_packet+1):((i1)*samples_per_packet))= typecast(rawData(3:end),'int16');
    catch
        disp('receive timed out?');
    end
end

% this is the only change now, what used to be
%datafloat = double(fftdata);
%is now
datafloat = double(fftdata(2:2:end)) + sqrt(-1)*(double(fftdata(1:2:end)));

% this below line takes "datafloat", which is a floating point
% representation of the raw data which we collected, and does a few things
% 1) data is windowed. (for when signal is not at bin center)
% 2) a small amount of noise is added.  This keeps any bins from being 0
% and messing up the plot by trying to take log(0).  It also raises the
% noise floor above the fixed pattern noise of our DDS, and keeps the plot
% "moving" so that you know that it is working (if everything stays the
% same is is very disconcerting!)
% 3) fft is taken
% 4) magnitude of that FFT is taken
% 5) result is plotted in dB, with freqs_khz on the axis
subplot(2,1,1);
plot(freqs,20*log10((abs(fft(((datafloat+randn(1,length(datafloat))).*hann(length(datafloat))'))))));
axis([0 fs -40 150]); 
xlabel('Frequency Hz')
subplot(2,1,2);
plot(real(datafloat));
hold on;
plot(imag(datafloat),'r');
hold off;
%toc;
drawnow;
    
end % while loop
    
    % reduce the buffer size so that packets are dropped until the next
    % data sequence is collected\
    
socket.setReceiveBufferSize(1);
socket.close();

