#include <sys/types.h>
#include <time.h>

enum {
    TCP = SOCK_STREAM,
    UDP = SOCK_DGRAM,
    N_CONNECTIONS = 10,
    TCP_PORT = 80,
    UDP_PORT = 1111,
};

struct payload {
    int packet_id;
    struct timespec sent;
    struct timespec received;
    struct timespec response;
};
