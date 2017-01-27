#include <sys/types.h>
#include <time.h>

enum {
    TCP = SOCK_STREAM,
    UDP = SOCK_DGRAM,
    TCP_PORT = 80,
    UDP_PORT = 1111,
    CLIENT_BASE_PORT = 1024,
};

struct payload {
    int packet_id;
    struct timespec sent;
    struct timespec received;
    struct timespec response;
};
