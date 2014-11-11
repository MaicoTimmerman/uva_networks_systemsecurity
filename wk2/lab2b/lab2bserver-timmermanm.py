## Netwerken en Systeembeveiliging Lab 2B - Chat Room (Server)
## NAME: Maico Timmerman
## STUDENT ID: 10542590

from select import select
from socket import socket
from socket import AF_INET, SOCK_STREAM, SO_REUSEADDR, SOL_SOCKET


class ChatServer():

    def __init__(self, port):

        # Initialize the enviroment
        print('Starting server on port {}'.format(port))
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        # Start the server
        self.socket.bind(('', port))
        self.listen(5)

        # Set up the lists for selection
        self.inputs = [self.socket, ]
        self.message_queue = {}
        self.start()

    def start(self):
        """
        Chat server entry point.
        port: The port to listen on.
        """

        while self.inputs:
            print('Waiting for the next event')
            input_ready, output_ready, except_ready = \
                select.select(self.inputs, [], [])

            # Some error happened at the socket,
            # remove it from the system entirely
            for sock in except_ready:
                self.remove_client(sock)

            # Sockets that are ready, are clients that are trying to connect.
            for sock in input_ready:

                # A new connection has been made.
                if sock == server:
                    # handle the server socket
                    client, address = server.accept()

                # Handle existing sockets
                else:
                    data = sock.recv(1024)
                    if data:
                        print('%s received from %s') % \
                            (data, sock.getsockname())
                        # self.handle_data(data, sock)

                    # No data has been send, thus the client has disconnected
                    else:
                        self.remove_client(sock)

            # Connections with output ready can be written to,
            # so send all messages in its queue.
            for sock in output_ready:
                self.handle_message_queue(sock)

        self.socket.close()

    # Remove the client from the list
    def remove_client(self, sock):
        try:
            sock.close()
            self.inputs.remove(sock)
            self.message_queue[sock.getsockname()].pop()
        except:
            print('An error happened while removing a client.')
        return

    def new_client(self, sock):
        self.inputs.append(sock)
        self.message_queue[sock.getsockname()] = ["Welcome to the chatserver"]
        print('New client added: %s') % str(sock.getsockname())


    def broadcast_message(self, msg):
        return

    def handle_message_queue(self, sock):
        return

    def help(self):
        help_str = ''
        help_str += '/nick <user>          | Change nickname to <user>\n'
        help_str += '/say <text>           | Send message to all users\n'
        help_str += '/whisper <user> <text>| Send private message to <user>\n'
        help_str += '/list                 | Lists all online users\n'
        return help_str


## Command line parser.
if __name__ == '__main__':
    import sys
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--port', help='port to listen on', default=12345, type=int)
    args = p.parse_args(sys.argv[1:])

    server = ChatServer(args.port)
