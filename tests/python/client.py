import gevent
import json
import sys
import time

from gevent import socket

BASE_PORT = 5000

def communicate_tcp(id):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((sys.argv[1], BASE_PORT + id))
        s.connect((sys.argv[2], 4999))
        payload = {"id": id, "ping": time.time()}
        s.sendall(json.dumps(payload).encode())
        data = s.recv(4096)
        payload = json.loads(data.decode())
        payload["response"] = time.time()
        print(payload)
        s.close()

connections = [gevent.spawn(communicate_tcp, i) for i in range(int(sys.argv[3]))]
gevent.joinall(connections)
