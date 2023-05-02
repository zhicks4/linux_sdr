#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h> 
#include <fcntl.h> 
#include <unistd.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <string.h>
#define _BSD_SOURCE

// Radio FIFO register locations
#define FIFO_BASE_ADDR 0x43c10000
#define FIFO_DATA_OFFSET 0
#define FIFO_COUNT_OFFSET 1

volatile unsigned int * get_a_pointer(unsigned int phys_addr) {
	int mem_fd = open("/dev/mem", O_RDWR | O_SYNC); 
	void *map_base = mmap(0, 4096, PROT_READ | PROT_WRITE, MAP_SHARED, mem_fd, phys_addr); 
	volatile unsigned int *radio_base = (volatile unsigned int *)map_base; 
	return (radio_base);
}

int main(int argc, char* argv[]) {
    // Open memory mapped FIFO registers
    volatile unsigned int *fifoBase = get_a_pointer(FIFO_BASE_ADDR);
    
    // Initialize FIFO data & UDP packet variables
    int32_t sample;
    int16_t sample_I, sample_Q;
    int16_t udpBuff[513] = {0};
    uint16_t idx = 1;
    int16_t seqNum = 0;
    
    // Create socket
    int socket_desc = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    struct sockaddr_in dest_addr;
    int dest_addr_len = sizeof(dest_addr);

    // Set port and IP
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_port = htons(strtol(argv[2], NULL, 10)); // UDP port
    dest_addr.sin_addr.s_addr = inet_addr(argv[1]); // IP address
    
    // Main loop
    unsigned int count = fifoBase[FIFO_COUNT_OFFSET];
    while(1) {
        if (count > 0) {
            sample = fifoBase[FIFO_DATA_OFFSET];
            sample_I = (int16_t)(sample & 0x0000FFFF);
            sample_Q = (int16_t)((sample & 0xFFFF0000) >> 16);
            udpBuff[idx++] = sample_I;
            udpBuff[idx++] = sample_Q;
            if (idx > 512) {
                // send packet
                sendto(socket_desc, udpBuff, sizeof(udpBuff), 0, (struct sockaddr*)&dest_addr, dest_addr_len);
                // clear buffer, reset index
                memset(udpBuff, 0, sizeof(udpBuff));
                idx = 0;
                // set new sequence number
                seqNum++;
                udpBuff[idx++] = seqNum;
            }
        }
        count = fifoBase[FIFO_COUNT_OFFSET];
    }
}