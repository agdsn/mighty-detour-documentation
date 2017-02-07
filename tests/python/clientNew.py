import sys
from gevent import socket
import ipaddress
import itertools
import gevent


BASE_PORT = int(sys.argv[2])
NETWORK = ipaddress.ip_network(sys.argv[1])


def getIP(id):
    return str(next(itertools.islice(NETWORK.hosts(), id, id + 1)))

def setUpUDP(id):
    address = (sys.argv[3], int(sys.argv[4]))
    message = 'Hello World! ' + str(id)
    s = socket.socket(type=socket.SOCK_DGRAM)
    tmp = (getIP(id), BASE_PORT)
    s.bind(tmp)
    s.connect(address)
    while True:
        s.send(message.encode())
        data, address = s.recvfrom(8192)
        print(data.decode())

connections = [gevent.spawn(setUpUDP, i) for i in range(10)]
gevent.joinall(connections)
