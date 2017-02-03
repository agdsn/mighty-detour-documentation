#include <arpa/inet.h>
#include <assert.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

#include <shared.h>

int create_socket(int type);
void init_tcp_socket(int socket_tcp, int n_connections);
void init_udp_socket(int socket_udp);
void process_tcp_packet(int socket_tcp);
void process_udp_packet(int socket_udp);

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "server: usage: ./server #CONNECTIONS\n");
        return EXIT_FAILURE;
    }
    int n_connections = 0;
    if (sscanf(argv[1], "%u", &n_connections) != 1) {
        fprintf(stderr, "server: invalid input %s\n", argv[1]);
        return EXIT_FAILURE;
    }
    int socket_tcp = create_socket(TCP);
    int socket_udp = create_socket(UDP);
    init_tcp_socket(socket_tcp, n_connections);
    init_udp_socket(socket_udp);
    // TODO parallelise
    for (int i = 0; i < n_connections; ++i) {
        process_tcp_packet(socket_tcp);
        process_udp_packet(socket_udp);
    }
    close(socket_tcp);
    close(socket_udp);
    return 0;
}

int create_socket(int type) {
    int new_socket = socket(AF_INET, type, 0);
    if (new_socket < 0) {
        perror("server: Creating socket");
        exit(EXIT_FAILURE);
    }
    return new_socket;
}

void init_tcp_socket(int socket_tcp, int n_connections) {
    struct sockaddr_in server = {.sin_family = AF_INET, .sin_port = htons(TCP_PORT),
                                 .sin_addr.s_addr = htonl(INADDR_ANY)};
    int success = bind(socket_tcp, (struct sockaddr *) &server, sizeof server);
    if (success < 0) {
        perror("server: Binding socket");
        exit(EXIT_FAILURE);
    }
    success = listen(socket_tcp, n_connections);
    if (success < 0) {
        perror("server: Listening on socket");
        exit(EXIT_FAILURE);
    }
}

void init_udp_socket(int socket_udp) {
    struct sockaddr_in server = {.sin_family = AF_INET, .sin_port = htons(UDP_PORT),
                                 .sin_addr.s_addr = htonl(INADDR_ANY)};
    int success = bind(socket_udp, (struct sockaddr *) &server, sizeof server);
    if (success < 0) {
        perror("server: Binding socket");
        exit(EXIT_FAILURE);
    }
}

void process_tcp_packet(int socket_tcp) {
    struct sockaddr_in client = {0};
    int client_len = sizeof client;
    int socket_rcv =
            accept(socket_tcp, (struct sockaddr *) &client, &client_len);
    if (socket_rcv < 0) {
        perror("server: Accepting connection");
        exit(EXIT_FAILURE);
    }
    struct payload data;
    recv(socket_rcv, &data, sizeof data, 0);
    if (clock_gettime(CLOCK_MONOTONIC, &data.received) < 0) {
        perror("server: Storing system time");
        exit(EXIT_FAILURE);
    }
    data.received.tv_sec = time(NULL);
    printf("id: %d\n"
           "sent: %s\t%ld ns\n"
           "arrived: %s\t%ld ns\n",
           data.packet_id,
           asctime(localtime(&data.sent.tv_sec)),
           data.sent.tv_nsec,
           asctime(localtime(&data.received.tv_sec)),
           data.received.tv_nsec);
    send(socket_rcv, &data, sizeof data, 0);
    close(socket_rcv);
}

void process_udp_packet(int socket_udp) {
    struct sockaddr_in client = {0};
    int client_len = sizeof client;
    struct payload data;
    recvfrom(socket_udp, &data, sizeof data, 0, (struct sockaddr *) &client, &client_len);
    if (clock_gettime(CLOCK_MONOTONIC, &data.received) < 0) {
        perror("server: Storing system time");
        exit(EXIT_FAILURE);
    }
    data.received.tv_sec = time(NULL);
    printf("id: %d\n"
           "sent: %s\t%ld ns\n"
           "arrived: %s\t%ld ns\n",
           data.packet_id,
           asctime(localtime(&data.sent.tv_sec)),
           data.sent.tv_nsec,
           asctime(localtime(&data.received.tv_sec)),
           data.received.tv_nsec);
    sendto(socket_udp, &data, sizeof data, 0, (struct sockaddr *) &client, client_len);
}
