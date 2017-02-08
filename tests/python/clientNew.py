from gevent.server import DatagramServer
import sys
import time
import json
from gevent import socket
import ipaddress
import itertools
import gevent
import os


BASE_PORT = int(sys.argv[2])
NETWORK = ipaddress.ip_network(sys.argv[1])
NETWORKS = NETWORK.subnets(new_prefix=24)


class ReceiveServer(DatagramServer):

    def handle(self, data, address):
        print("Handle")
        tmp = time.time()
        payload = json.loads(data.decode())
        payload["pongRecv"] = tmp
        print(payload)


def spawnServer(port):
    print("Server up on port: " + str(500 + port))
    ReceiveServer(':' + str(port + 500)).serve_forever()

def getIP(net, id):
    return str(next(itertools.islice(net.hosts(), id, id + 1)))

def setUpUDP(net, port, id):
    address = (sys.argv[3], port)

    s = socket.socket(type=socket.SOCK_DGRAM)
    tmp = (getIP(net, id), port)
    s.bind(tmp)
    s.connect(address)
    print(tmp)
    #ReceiveServer(':' + str(port + 500)).serve_forever()
    #print("Server up")
    while True:
        payload = {"id": id, "ping": time.time()}
        s.send(json.dumps(payload).encode())
        gevent.sleep()

connections = []
servers = []
port = BASE_PORT
for net in NETWORKS:
    servers += [gevent.spawn(spawnServer, port)]
    connections += [gevent.spawn(setUpUDP, net, port, i) for i in range(10)]
    port += 1

gevent.joinall(connections)
