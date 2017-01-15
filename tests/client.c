#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>

#include <shared.h>

int create_socket(int type);
void init_tcp_connection(int socket_tcp, const char *ip_address);
void communicate_tcp(int socket_tcp, int packet_id);
void communicate_udp(int socket_udp, int packet_id, const char *ip_address);

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "client: No server ip address given");
        return EXIT_FAILURE;
    }
    int socket_tcp = create_socket(TCP);
    int socket_udp = create_socket(UDP);
    init_tcp_connection(socket_tcp, argv[1]);
    communicate_tcp(socket_tcp, 42);
    communicate_udp(socket_udp, 23, argv[1]);
    close(socket_tcp);
    close(socket_udp);
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
