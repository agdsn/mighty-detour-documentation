import sys
from gevent.server import DatagramServer

PORT = sys.argv[1]


class EchoServer(DatagramServer):

    def handle(self, data, address):
        self.socket.sendto(('Received %s bytes' % len(data)).encode('utf-8'), address)
        print("Pong")


if __name__ == '__main__':
    print('Receiving datagrams on :' + str(PORT))
    EchoServer(':' + str(PORT)).serve_forever()