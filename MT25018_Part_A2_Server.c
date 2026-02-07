/*
 * MT25018 - Graduate Systems PA02
 * Part A2: One-Copy Implementation - Server
 * Uses sendmsg() with iovec to reduce one copy
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <sys/uio.h>
#include <errno.h>
#include <signal.h>

#define PORT 8080
#define MAX_CLIENTS 100
#define NUM_STRING_FIELDS 8

/* Message structure with 8 dynamically allocated string fields */
typedef struct {
    char *field1;
    char *field2;
    char *field3;
    char *field4;
    char *field5;
    char *field6;
    char *field7;
    char *field8;
} Message;

/* Thread arguments */
typedef struct {
    int client_socket;
    int message_size;
    int thread_id;
} ThreadArgs;

/* Global statistics */
typedef struct {
    long long total_bytes_sent;
    long long total_messages_sent;
    struct timeval start_time;
    pthread_mutex_t stats_mutex;
} ServerStats;

ServerStats global_stats = {0, 0, {0, 0}, PTHREAD_MUTEX_INITIALIZER};
volatile int server_running = 1;

/* Allocate message with heap-allocated string fields (pre-registered buffers) */
Message* allocate_message(int field_size) {
    Message *msg = (Message *)malloc(sizeof(Message));
    if (!msg) {
        perror("malloc failed for Message");
        return NULL;
    }
    
    /* Allocate each field on heap - these are pre-registered buffers */
    msg->field1 = (char *)malloc(field_size);
    msg->field2 = (char *)malloc(field_size);
    msg->field3 = (char *)malloc(field_size);
    msg->field4 = (char *)malloc(field_size);
    msg->field5 = (char *)malloc(field_size);
    msg->field6 = (char *)malloc(field_size);
    msg->field7 = (char *)malloc(field_size);
    msg->field8 = (char *)malloc(field_size);
    
    if (!msg->field1 || !msg->field2 || !msg->field3 || !msg->field4 ||
        !msg->field5 || !msg->field6 || !msg->field7 || !msg->field8) {
        perror("malloc failed for message fields");
        free(msg->field1); free(msg->field2); free(msg->field3); free(msg->field4);
        free(msg->field5); free(msg->field6); free(msg->field7); free(msg->field8);
        free(msg);
        return NULL;
    }
    
    /* Fill with dummy data */
    for (int i = 0; i < field_size - 1; i++) {
        msg->field1[i] = 'A' + (i % 26);
        msg->field2[i] = 'B' + (i % 26);
        msg->field3[i] = 'C' + (i % 26);
        msg->field4[i] = 'D' + (i % 26);
        msg->field5[i] = 'E' + (i % 26);
        msg->field6[i] = 'F' + (i % 26);
        msg->field7[i] = 'G' + (i % 26);
        msg->field8[i] = 'H' + (i % 26);
    }
    msg->field1[field_size - 1] = '\0';
    msg->field2[field_size - 1] = '\0';
    msg->field3[field_size - 1] = '\0';
    msg->field4[field_size - 1] = '\0';
    msg->field5[field_size - 1] = '\0';
    msg->field6[field_size - 1] = '\0';
    msg->field7[field_size - 1] = '\0';
    msg->field8[field_size - 1] = '\0';
    
    return msg;
}

/* Free message and its heap-allocated fields */
void free_message(Message *msg) {
    if (msg) {
        free(msg->field1);
        free(msg->field2);
        free(msg->field3);
        free(msg->field4);
        free(msg->field5);
        free(msg->field6);
        free(msg->field7);
        free(msg->field8);
        free(msg);
    }
}

/* Send message using sendmsg() with iovec - one-copy approach
 * This eliminates one copy by using scatter-gather I/O
 * The kernel can directly access the pre-registered buffers without
 * an intermediate copy to a contiguous buffer
 */
int send_message_onecopy(int socket, Message *msg, int field_size) {
    struct iovec iov[NUM_STRING_FIELDS];
    struct msghdr msghdr;
    
    /* Setup iovec array pointing to pre-registered buffers */
    iov[0].iov_base = msg->field1;
    iov[0].iov_len = field_size;
    iov[1].iov_base = msg->field2;
    iov[1].iov_len = field_size;
    iov[2].iov_base = msg->field3;
    iov[2].iov_len = field_size;
    iov[3].iov_base = msg->field4;
    iov[3].iov_len = field_size;
    iov[4].iov_base = msg->field5;
    iov[4].iov_len = field_size;
    iov[5].iov_base = msg->field6;
    iov[5].iov_len = field_size;
    iov[6].iov_base = msg->field7;
    iov[6].iov_len = field_size;
    iov[7].iov_base = msg->field8;
    iov[7].iov_len = field_size;
    
    /* Setup message header */
    memset(&msghdr, 0, sizeof(msghdr));
    msghdr.msg_iov = iov;
    msghdr.msg_iovlen = NUM_STRING_FIELDS;
    
    /* Send using sendmsg - kernel performs scatter-gather I/O */
    ssize_t bytes_sent = sendmsg(socket, &msghdr, 0);
    
    return bytes_sent;
}

/* Client handler thread */
void* client_handler(void *args) {
    ThreadArgs *thread_args = (ThreadArgs *)args;
    int client_socket = thread_args->client_socket;
    int message_size = thread_args->message_size;
    int field_size = message_size / NUM_STRING_FIELDS;
    
    printf("[Thread %d] Started handling client, field_size=%d bytes\n", 
           thread_args->thread_id, field_size);
    
    /* Allocate message structure with pre-registered buffers */
    Message *msg = allocate_message(field_size);
    if (!msg) {
        close(client_socket);
        free(thread_args);
        return NULL;
    }
    
    long long local_bytes = 0;
    long long local_messages = 0;
    
    /* Send messages continuously until client disconnects */
    while (server_running) {
        int bytes_sent = send_message_onecopy(client_socket, msg, field_size);
        if (bytes_sent < 0) {
            if (errno == EPIPE || errno == ECONNRESET) {
                break; /* Client disconnected */
            }
            perror("sendmsg failed");
            break;
        }
        
        local_bytes += bytes_sent;
        local_messages++;
        
        /* Update global stats periodically */
        if (local_messages % 1000 == 0) {
            pthread_mutex_lock(&global_stats.stats_mutex);
            global_stats.total_bytes_sent += local_bytes;
            global_stats.total_messages_sent += local_messages;
            pthread_mutex_unlock(&global_stats.stats_mutex);
            local_bytes = 0;
            local_messages = 0;
        }
    }
    
    /* Final stats update */
    pthread_mutex_lock(&global_stats.stats_mutex);
    global_stats.total_bytes_sent += local_bytes;
    global_stats.total_messages_sent += local_messages;
    pthread_mutex_unlock(&global_stats.stats_mutex);
    
    printf("[Thread %d] Client disconnected. Messages sent: %lld\n", 
           thread_args->thread_id, local_messages);
    
    free_message(msg);
    close(client_socket);
    free(thread_args);
    return NULL;
}

/* Signal handler for graceful shutdown */
void signal_handler(int signum) {
    (void)signum;  /* Unused parameter */
    printf("\nShutdown signal received. Stopping server...\n");
    server_running = 0;
}

int main(int argc, char *argv[]) {
    if (argc != 3) {
        fprintf(stderr, "Usage: %s <message_size> <max_threads>\n", argv[0]);
        fprintf(stderr, "  message_size: Total message size in bytes (must be multiple of 8)\n");
        fprintf(stderr, "  max_threads: Maximum number of client threads\n");
        exit(EXIT_FAILURE);
    }
    
    int message_size = atoi(argv[1]);
    int max_threads = atoi(argv[2]);
    
    if (message_size % NUM_STRING_FIELDS != 0) {
        fprintf(stderr, "Error: message_size must be divisible by %d\n", NUM_STRING_FIELDS);
        exit(EXIT_FAILURE);
    }
    
    printf("=== MT25018 Part A2 Server (One-Copy) ===\n");
    printf("Message size: %d bytes (%d bytes per field)\n", 
           message_size, message_size / NUM_STRING_FIELDS);
    printf("Max threads: %d\n", max_threads);
    printf("Using sendmsg() with iovec for scatter-gather I/O\n");
    
    /* Setup signal handlers */
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    
    /* Create server socket */
    int server_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (server_socket < 0) {
        perror("socket creation failed");
        exit(EXIT_FAILURE);
    }
    
    /* Set socket options */
    int opt = 1;
    if (setsockopt(server_socket, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        perror("setsockopt failed");
        exit(EXIT_FAILURE);
    }
    
    /* Bind socket */
    struct sockaddr_in server_addr;
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);
    
    if (bind(server_socket, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("bind failed");
        exit(EXIT_FAILURE);
    }
    
    /* Listen for connections */
    if (listen(server_socket, max_threads) < 0) {
        perror("listen failed");
        exit(EXIT_FAILURE);
    }
    
    printf("Server listening on port %d...\n", PORT);
    gettimeofday(&global_stats.start_time, NULL);
    
    /* Accept clients and create threads */
    int thread_count = 0;
    pthread_t threads[MAX_CLIENTS];
    
    while (server_running && thread_count < max_threads) {
        struct sockaddr_in client_addr;
        socklen_t client_len = sizeof(client_addr);
        
        int client_socket = accept(server_socket, (struct sockaddr *)&client_addr, &client_len);
        if (client_socket < 0) {
            if (server_running) {
                perror("accept failed");
            }
            continue;
        }
        
        printf("Client %d connected from %s:%d\n", 
               thread_count + 1,
               inet_ntoa(client_addr.sin_addr),
               ntohs(client_addr.sin_port));
        
        /* Create thread arguments */
        ThreadArgs *args = (ThreadArgs *)malloc(sizeof(ThreadArgs));
        args->client_socket = client_socket;
        args->message_size = message_size;
        args->thread_id = thread_count + 1;
        
        /* Create client handler thread */
        if (pthread_create(&threads[thread_count], NULL, client_handler, args) != 0) {
            perror("pthread_create failed");
            close(client_socket);
            free(args);
            continue;
        }
        
        pthread_detach(threads[thread_count]);
        thread_count++;
    }
    
    printf("Maximum threads reached or shutdown requested. Waiting for clients...\n");
    
    /* Wait for all threads to complete */
    sleep(2);
    
    /* Print final statistics */
    struct timeval end_time;
    gettimeofday(&end_time, NULL);
    double elapsed = (end_time.tv_sec - global_stats.start_time.tv_sec) + 
                     (end_time.tv_usec - global_stats.start_time.tv_usec) / 1000000.0;
    
    printf("\n=== Server Statistics ===\n");
    printf("Total bytes sent: %lld\n", global_stats.total_bytes_sent);
    printf("Total messages sent: %lld\n", global_stats.total_messages_sent);
    printf("Elapsed time: %.2f seconds\n", elapsed);
    printf("Throughput: %.2f Gbps\n", 
           (global_stats.total_bytes_sent * 8.0) / (elapsed * 1e9));
    
    close(server_socket);
    pthread_mutex_destroy(&global_stats.stats_mutex);
    
    return 0;
}
