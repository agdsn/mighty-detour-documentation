#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>

#include <shared.h>

int create_socket(int type);
void bind_socket(int socket_id, const char *ip_address, int port);
void init_tcp_connection(int socket_tcp, const char *ip_address);
void communicate_tcp(int socket_tcp, int packet_id);
void communicate_udp(int socket_udp, int packet_id, const char *ip_address);

int main(int argc, char *argv[]) {
    if (argc != 4) {
        fprintf(stderr, "client: usage: ./client SADDR DADDR #CONNECTIONS\n");
        return EXIT_FAILURE;
    }
    int n_connections = 0;
    if (sscanf(argv[3], "%u", &n_connections) != 1) {
        fprintf(stderr, "client: invalid input %s\n", argv[3]);
        return EXIT_FAILURE;
    }
    int tcp_sockets[n_connections];
    int udp_sockets[n_connections];
    for (int i = 0; i < n_connections; ++i) {
        tcp_sockets[i] = create_socket(TCP);
        udp_sockets[i] = create_socket(UDP);
        bind_socket(tcp_sockets[i], argv[1], CLIENT_BASE_PORT + i);
        bind_socket(udp_sockets[i], argv[1], CLIENT_BASE_PORT + n_connections + i);
    }
    // TODO parallelise
    for (int i = 0; i < n_connections; ++i) {
        init_tcp_connection(tcp_sockets[i], argv[2]);
        communicate_tcp(tcp_sockets[i], tcp_sockets[i]);
        communicate_udp(udp_sockets[i], udp_sockets[i], argv[2]);
        close(tcp_sockets[i]);
        close(udp_sockets[i]);
    }
    return 0;
}

int create_socket(int type) {
    int new_socket = socket(AF_INET, type, 0);
    if (new_socket < 0) {
        perror("client: Creating socket");
        exit(EXIT_FAILURE);
    }
    return new_socket;
}

void bind_socket(int socket_id, const char *ip_address, int port) {
    struct sockaddr_in client = {.sin_family = AF_INET,
                                 .sin_port = port};
    int success = inet_aton(ip_address, &client.sin_addr);
    if (!success) {
        fprintf(stderr,
                "client: Binding local socket: Invalid IP address %s\n",
                ip_address);
        exit(EXIT_FAILURE);
    }
    success = bind(socket_id, (struct sockaddr *) &client, sizeof client);
    if (success < 0) {
        perror("client: Binding socket");
        exit(EXIT_FAILURE);
    }
}

void init_tcp_connection(int socket_tcp, const char *ip_address) {
    struct sockaddr_in server = {.sin_family = AF_INET, .sin_port = htons(80)};
    int success = inet_aton(ip_address, &server.sin_addr);
    if (!success) {
        fprintf(stderr,
                "client: Connecting to server: Invalid IP address %s\n",
                ip_address);
        exit(EXIT_FAILURE);
    }
    success = connect(socket_tcp, (struct sockaddr *) &server, sizeof server);
    if (success < 0) {
        perror("client: Connecting to server");
        exit(EXIT_FAILURE);
    }
}

void communicate_tcp(int socket_tcp, int packet_id) {
    struct payload data = {.packet_id = packet_id};
    if (clock_gettime(CLOCK_MONOTONIC, &data.sent) < 0) {
        perror("client: Storing system time");
        exit(EXIT_FAILURE);
    }
    data.sent.tv_sec = time(NULL);
    send(socket_tcp, &data, sizeof data, 0);
    recv(socket_tcp, &data, sizeof data, 0);
    if (clock_gettime(CLOCK_MONOTONIC, &data.response) < 0) {
        perror("client: Storing system time");
        exit(EXIT_FAILURE);
    }
    data.response.tv_sec = time(NULL);
    printf("id: %d\n"
           "sent: %s\t%ld ns\n"
           "arrived: %s\t%ld ns\n"
           "response received: %s\t%ld ns\n",
           data.packet_id,
           asctime(localtime(&data.sent.tv_sec)),
           data.sent.tv_nsec,
           asctime(localtime(&data.received.tv_sec)),
           data.received.tv_nsec,
           asctime(localtime(&data.response.tv_sec)),
           data.response.tv_nsec);
}

void communicate_udp(int socket_udp, int packet_id, const char *ip_address) {
    struct sockaddr_in server = {.sin_family = AF_INET, .sin_port = htons(UDP_PORT)};
    int server_len = sizeof server;
    int success = inet_aton(ip_address, &server.sin_addr);
    if (!success) {
        fprintf(stderr,
                "client: Connecting to server: Invalid IP address %s\n",
                ip_address);
        exit(EXIT_FAILURE);
    }
    struct payload data = {.packet_id = packet_id};
    if (clock_gettime(CLOCK_MONOTONIC, &data.sent) < 0) {
        perror("client: Storing system time");
        exit(EXIT_FAILURE);
    }
    data.sent.tv_sec = time(NULL);
    sendto(socket_udp, &data, sizeof data, 0, (struct sockaddr *) &server, server_len);
    recvfrom(socket_udp, &data, sizeof data, 0, (struct sockaddr *) &server, &server_len);
    if (clock_gettime(CLOCK_MONOTONIC, &data.response) < 0) {
        perror("client: Storing system time");
        exit(EXIT_FAILURE);
    }
    data.response.tv_sec = time(NULL);
    printf("id: %d\n"
           "sent: %s\t%ld ns\n"
           "arrived: %s\t%ld ns\n"
           "response received: %s\t%ld ns\n",
           data.packet_id,
           asctime(localtime(&data.sent.tv_sec)),
           data.sent.tv_nsec,
           asctime(localtime(&data.received.tv_sec)),
           data.received.tv_nsec,
           asctime(localtime(&data.response.tv_sec)),
           data.response.tv_nsec);
}
