## Netwerken en Systeembeveiliging Lab 2B - Chat Room (Client)
## NAME: Maico Timmerman
## STUDENT ID: 10542590

import socket
from select import select
from socket import AF_INET, SOCK_STREAM, SO_REUSEADDR, SOL_SOCKET
from gui import MainWindow


class ChatClient():

    def __init__(self, port, cert):
        """
        Initialize a chatclient
        port: port to connect to.
        cert: public certificate (bonus task)
        """

        # Initialize the enviroment
        self.win = MainWindow()

        self.socket = socket.socket(AF_INET, SOCK_STREAM)
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.socket.connect(('localhost', port))
        self.inputs = [self.socket, ]
        self.connected = True

        self.start()

    def start(self):
        """
        Main loop of sending and receiving.
        """
        # The following code explains how to use the GUI.
        # update() returns false when the user quits or presses escape.
        while self.win.update():

            if self.connected:
                input_ready, output_ready, except_ready = \
                    select(self.inputs, [], [], 0)
                for sock in input_ready:
                    data = sock.recv(1024)
                    if not data:
                        sock.close()
                        self.connected = False
                        self.win.writeln('Server disconnected')
                    else:
                        self.win.writeln(data)

            # if the user entered a line getline() returns a string.
            line = self.win.getline()
            if line:
                self.win.writeln(line)
                if self.connected:
                    self.socket.send(line)


## Command line parser.
if __name__ == '__main__':
    import sys
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--port', help='port to connect to',
                   default=12345, type=int)
    p.add_argument('--cert', help='server public cert',
                   default='')
    args = p.parse_args(sys.argv[1:])

    client = ChatClient(args.port, args.cert)
