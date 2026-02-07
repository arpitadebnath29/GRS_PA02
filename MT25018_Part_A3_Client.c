/*
 * MT25018 - Graduate Systems PA02
 * Part A3: Zero-Copy Implementation - Client
 * Standard recv() on client side (zero-copy is primarily server-side optimization)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <errno.h>
#include <time.h>

#define PORT 8080
#define NUM_STRING_FIELDS 8

/* Client statistics */
typedef struct {
    long long total_bytes_received;
    long long total_messages_received;
    double total_latency_us;
    long long latency_samples;
} ClientStats;

/* Receive message - client uses standard recv()
 * Zero-copy optimization is primarily on the send side
 */
int recv_message(int socket, int field_size) {
    char *buffer = (char *)malloc(field_size);
    if (!buffer) {
        perror("malloc failed");
        return -1;
    }
    
    int total_received = 0;
    
    /* Receive all 8 fields */
    for (int i = 0; i < NUM_STRING_FIELDS; i++) {
        int bytes_received = 0;
        while (bytes_received < field_size) {
            int n = recv(socket, buffer + bytes_received, field_size - bytes_received, 0);
            if (n <= 0) {
                free(buffer);
                return -1;
            }
            bytes_received += n;
        }
        total_received += bytes_received;
    }
    
    free(buffer);
    return total_received;
}

/* Get current time in microseconds */
long long get_time_us() {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (long long)tv.tv_sec * 1000000 + tv.tv_usec;
}

int main(int argc, char *argv[]) {
    if (argc != 4) {
        fprintf(stderr, "Usage: %s <server_ip> <message_size> <duration_seconds>\n", argv[0]);
        fprintf(stderr, "  server_ip: IP address of the server\n");
        fprintf(stderr, "  message_size: Total message size in bytes (must be multiple of 8)\n");
        fprintf(stderr, "  duration_seconds: How long to run the test\n");
        exit(EXIT_FAILURE);
    }
    
    char *server_ip = argv[1];
    int message_size = atoi(argv[2]);
    int duration = atoi(argv[3]);
    int field_size = message_size / NUM_STRING_FIELDS;
    
    if (message_size % NUM_STRING_FIELDS != 0) {
        fprintf(stderr, "Error: message_size must be divisible by %d\n", NUM_STRING_FIELDS);
        exit(EXIT_FAILURE);
    }
    
    printf("=== MT25018 Part A3 Client (Zero-Copy) ===\n");
    printf("Server IP: %s\n", server_ip);
    printf("Message size: %d bytes (%d bytes per field)\n", message_size, field_size);
    printf("Duration: %d seconds\n", duration);
    printf("Note: Zero-copy optimization is on server side\n");
    
    /* Create socket */
    int client_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (client_socket < 0) {
        perror("socket creation failed");
        exit(EXIT_FAILURE);
    }
    
    /* Setup server address */
    struct sockaddr_in server_addr;
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    
    if (inet_pton(AF_INET, server_ip, &server_addr.sin_addr) <= 0) {
        perror("Invalid address");
        exit(EXIT_FAILURE);
    }
    
    /* Connect to server */
    printf("Connecting to server...\n");
    if (connect(client_socket, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("connection failed");
        exit(EXIT_FAILURE);
    }
    printf("Connected successfully!\n\n");
    
    /* Initialize statistics */
    ClientStats stats = {0, 0, 0.0, 0};
    
    /* Record start time */
    long long start_time = get_time_us();
    long long end_time = start_time + (duration * 1000000LL);
    
    /* Receive messages for specified duration */
    printf("Receiving data...\n");
    while (get_time_us() < end_time) {
        long long msg_start = get_time_us();
        
        int bytes_received = recv_message(client_socket, field_size);
        if (bytes_received < 0) {
            if (errno == ECONNRESET) {
                printf("Server closed connection\n");
                break;
            }
            perror("recv failed");
            break;
        }
        
        long long msg_end = get_time_us();
        
        stats.total_bytes_received += bytes_received;
        stats.total_messages_received++;
        
        /* Sample latency every 100 messages to avoid overhead */
        if (stats.total_messages_received % 100 == 0) {
            stats.total_latency_us += (msg_end - msg_start);
            stats.latency_samples++;
        }
        
        /* Print progress every 10000 messages */
        if (stats.total_messages_received % 10000 == 0) {
            double elapsed = (get_time_us() - start_time) / 1000000.0;
            double throughput_gbps = (stats.total_bytes_received * 8.0) / (elapsed * 1e9);
            printf("Progress: %lld messages, %.2f Gbps\n", 
                   stats.total_messages_received, throughput_gbps);
        }
    }
    
    /* Calculate final statistics */
    long long actual_end = get_time_us();
    double elapsed_seconds = (actual_end - start_time) / 1000000.0;
    
    printf("\n=== Client Statistics ===\n");
    printf("Total bytes received: %lld\n", stats.total_bytes_received);
    printf("Total messages received: %lld\n", stats.total_messages_received);
    printf("Elapsed time: %.2f seconds\n", elapsed_seconds);
    printf("Throughput: %.2f Gbps\n", 
           (stats.total_bytes_received * 8.0) / (elapsed_seconds * 1e9));
    printf("Average throughput: %.2f MB/s\n", 
           (stats.total_bytes_received / (1024.0 * 1024.0)) / elapsed_seconds);
    
    if (stats.latency_samples > 0) {
        double avg_latency = stats.total_latency_us / stats.latency_samples;
        printf("Average latency: %.2f µs\n", avg_latency);
    }
    
    close(client_socket);
    return 0;
}
