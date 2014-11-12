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
        self.socket.listen(5)

        # Set up the lists for selection
        self.inputs = [self.socket, ]

        # dictionary of nicknames
        self.nicknames = {}
        self.user_no = 0

        # Server dict with variables linked to functions
        self.function_dict = {
            "/nick": self.set_nick,
            "/say": self.send_message,
            "/whisper": self.whisper_message,
            "/w": self.whisper_message,
            "/list": self.list_users,
            "/help": self.help,
            "/quit": self.remove_client
        }
        self.start()

    def start(self):
        """
        Chat server entry point.
        port: The port to listen on.
        """

        while self.inputs:
            # Determine which sockets have send things
            input_ready, output_ready, except_ready = \
                select(self.inputs, [], [])

            # Some error happened at the socket,
            # remove it from the system entirely
            for sock in except_ready:
                self.remove_client(sock)

            # Sockets that are ready, are clients that are trying to connect.
            for sock in input_ready:

                # A new connection has been made.
                if sock == self.socket:
                    # handle the server socket
                    client, address = self.socket.accept()
                    self.new_client(client)

                # Handle existing sockets
                else:
                    data = sock.recv(1024)
                    if data:
                        print('(%s, %s): "%s"') % \
                            (sock.getpeername()[1],
                             self.nicknames[sock.getpeername()[1]],
                             data)
                        self.handle_data(sock, data)

                    # No data has been send, thus the client has disconnected
                    else:
                        self.remove_client(sock)
        self.socket.close()

    def handle_data(self, sock, data):
        data_function = data.split(' ')[0]
        data_arguments = data.split(' ')[1:]
        try:
            self.function_dict[data_function](sock, *data_arguments)
        except KeyError:
            sock.send('I do not understand that command, use /help for' +
                      ' all available commands')
        except IndexError:
            sock.send('To few arguments for command %s' % data_function)

    def set_nick(self, sock, *args):
        """
        Set the nickname of the current connection to the new value.
        Broadcast to all the other members the new nickname.
        *args = (sock, new_nick, ....)
        """
        new_nick = args[0]
        old_nick = self.nicknames[sock.getpeername()[1]]

        # Test is the new_nick is not already taken by another client
        if (new_nick in self.nicknames.values()):
            sock.send('That nickname is already taken!')
            return

        # Set the new nick
        self.nicknames[sock.getpeername()[1]] = new_nick

        # Notify everyone that the nickname for this user has changed
        sock.send('Changed nick from %s to %s' % (old_nick, new_nick))
        self.broadcast_message(sock,
                               '%s changed nick to %s' % (old_nick, new_nick))

    def send_message(self, sock, *args):
        """
        Send a message to all other users
        *args = (word, word, word, ...)
        """
        msg = ' '.join(str(elem) for elem in args)
        msg = self.nicknames[sock.getpeername()[1]] + ': ' + msg
        self.broadcast_message(sock, msg)

    def whisper_message(self, sock, *args):
        """
        Send a message to a single user.
        *args = (user, word, word, ...)
        """

        # Find the socket matching the user
        user = args[0]
        sock_nr = self.nicknames.keys()[self.nicknames.values().index(user)]
        if (sock_nr == sock.getpeername()[1]):
            sock.send('Cannot send a whisper to self!')
            return

        msg = ' '.join(str(elem) for elem in args[1:])
        msg = '(w)' + self.nicknames[sock.getpeername()[1]] + ': ' + msg

        for recv_sock in self.inputs:
            if (recv_sock != self.socket):
                if recv_sock.getpeername()[1] == sock_nr:
                    recv_sock.send(msg)

    def list_users(self, sock, *args):
        user_list = ''

        # Iterate all sockets
        for user in self.inputs:

            # Dont display server socket
            if (user != self.socket and user != sock):
                user_list += self.nicknames[user.getpeername()[1]] + '\n'

            # Mark current user
            if (user == sock):
                user_list += '-> ' + \
                    self.nicknames[user.getpeername()[1]] + '\n'

        sock.send(user_list)

    def help(self, sock, *args):
        help_str = ''
        help_str += '/nick <user>           | Change nickname to <user>\n'
        help_str += '/say <text>            | Send message to all users\n'
        help_str += '/whisper <user> <text> | Send private message to <user>\n'
        help_str += '/w <user> <text> | Send private message to <user>\n'
        help_str += '/list                  | Lists all online users\n'
        sock.send(help_str)

    def new_client(self, sock):
        """ Add a client to the system. """
        # Set the nickname of the user
        print('Client added: %s') % str(sock.getpeername()[1])
        self.nicknames[sock.getpeername()[1]] = "User%s" % (self.user_no)
        self.user_no += 1

        self.broadcast_message(sock, '%s has joined the server!' %
                               self.nicknames[sock.getpeername()[1]])

        self.inputs.append(sock)
        sock.send("Welcome to the chatserver type /help for info!\n")

    def remove_client(self, sock):
        """ Remove a client from the system. """
        print('Client removed: %s') % str(sock.getpeername()[1])
        self.inputs.remove(sock)
        self.broadcast_message(sock, '%s has left the server!' %
                               self.nicknames[sock.getpeername()[1]])
        del self.nicknames[sock.getpeername()[1]]
        sock.close()

    def broadcast_message(self, sending_socket, msg):
        for sock in self.inputs:
            if (sock != self.socket and sock != sending_socket):
                print('Broadcast: %s' % msg)
                sock.send(msg)


## Command line parser.
if __name__ == '__main__':
    import sys
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--port', help='port to listen on', default=12345, type=int)
    args = p.parse_args(sys.argv[1:])

    server = ChatServer(args.port)
