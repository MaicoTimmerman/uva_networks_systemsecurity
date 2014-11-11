## Netwerken en Systeembeveiliging Lab 2B - Chat Room (Client)
## NAME: Maico Timmerman
## STUDENT ID: 10542590

import socket
from socket import AF_INET, SOCK_STREAM
from gui import MainWindow


class ChatClient():

    def __init__(self, port, cert):

        # Initialize the enviroment
        self.port = port
        self.cert = cert
        self.win = MainWindow()

        self.socket = socket(AF_INET, SOCK_STREAM)

    def loop(self, port, cert):
        """
        GUI loop.
        port: port to connect to.
        cert: public certificate (bonus task)
        """
        # The following code explains how to use the GUI.
        # update() returns false when the user quits or presses escape.
        while self.win.update():
            # if the user entered a line getline() returns a string.
            line = self.win.getline()
            if line:
                self.win.writeln(line)


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
