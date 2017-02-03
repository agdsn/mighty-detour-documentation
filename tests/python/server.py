import json
import time

from gevent import socket
from gevent.server import StreamServer

def communicate_tcp(sock, address):
    data = sock.recv(4096)
    payload = json.loads(data.decode())
    payload["pong"] = time.time()
    sock.sendall(json.dumps(payload).encode())
    sock.shutdown(socket.SHUT_WR)
    sock.close()

server = StreamServer(("", 4999), communicate_tcp)
server.serve_forever()
