import sys
import time
import json
from gevent import socket
from gevent.server import DatagramServer
import gevent
import gevent.queue

PORT = sys.argv[1]

class EchoServer(DatagramServer):

    queue = gevent.queue.Queue()

    def __init__(self, port):
        gevent.spawn(self.sendReplys)
        super(DatagramServer, self).__init__(port)

    def sendReplys(self):

        s = socket.socket(type=socket.SOCK_DGRAM)
        s.bind(("192.168.0.34", 9001))
        for item in self.queue:
            ip, port = item['address']
            port += 500
            s.connect((ip, port))
            item['message']["pongSend"] = time.time()
            print("Send response to:" + str(ip) + " " + str(port))
            s.sendall(json.dumps(item['message']).encode())

        s.shutdown(socket.SHUT_WR)
        s.close()


    def handle(self, data, address):
        tmp = time.time()
        payload = json.loads(data.decode())
        payload["pingRecv"] = tmp
        self.queue.put({ 'message': payload, 'address': address})


if __name__ == '__main__':
    print('Receiving datagrams on :' + str(PORT))
    EchoServer(':' + str(PORT)).serve_forever()
