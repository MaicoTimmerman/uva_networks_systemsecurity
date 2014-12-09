## Netwerken en Systeembeveiliging Lab 4 - Distributed Sensor Network
## NAME: Robin Klusman & Maico Timmerman
## STUDENT ID: 10675671
import struct
from math import sqrt
from copy import deepcopy
from threading import Timer
from select import select
from socket import socket, inet_aton
from socket import AF_INET, SO_REUSEADDR, SOL_SOCKET, SOCK_DGRAM, \
    IPPROTO_UDP, INADDR_ANY, IPPROTO_IP, IP_ADD_MEMBERSHIP, IP_MULTICAST_TTL
from random import randint
from gui import MainWindow
from sensor import message_encode, message_decode
from sensor import MSG_PING, MSG_PONG, MSG_ECHO, MSG_ECHO_REPLY, \
    OP_NOOP, OP_SIZE, OP_SUM, OP_MIN, OP_MAX


class SensorNode():

    def __init__(self, mcast_addr, sensor_pos, sensor_range, sensor_val,
                 grid_size, ping_period):
        """
        mcast_addr: udp multicast (ip, port) tuple.
        sensor_pos: (x,y) sensor position tuple.
        sensor_range: range of the sensor ping (radius).
        sensor_val: sensor value.
        grid_size: length of the  of the grid (which is always square).
        ping_period: time in seconds between multicast pings.
        """
        # Sequence number used for tracking echos
        self.echo_sequence = 0
        self.echos_recvd = []
        self.neighbours = {}
        self.echo_tracking = {}
        self.mcast_addr = mcast_addr
        self.sensor_pos = sensor_pos

        # self.sensor_range = sensor_range
        self.sensor_range = 150
        self.sensor_val = sensor_val
        self.grid_size = grid_size
        self.ping_period = ping_period
        self.fathers = {}

        # -- Create the multicast listener socket. --
        self.mcast = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)

        # Sets the socket address as reusable so you can run multiple instances
        # of the program on the same machine at the same time.
        self.mcast.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        # Subscribe the socket to multicast messages from the given address.
        self.mreq = struct.pack('4sl', inet_aton(mcast_addr[0]), INADDR_ANY)
        self.mcast.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, self.mreq)
        self.mcast.bind(mcast_addr)

        # -- Create the peer-to-peer socket. --
        self.peer = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)

        # Set the socket multicast TTL so it can send multicast messages.
        self.peer.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, 5)

        # Bind the socket to a random port.
        if sys.platform == 'win32':  # windows special case
            self.peer.bind(('localhost', INADDR_ANY))
        # should work for everything else
        else:
            self.peer.bind(('', INADDR_ANY))

        # -- make the gui --
        self._window = MainWindow()
        self._window.writeln('my address is %s:%s' % self.peer.getsockname())
        self._window.writeln('my position is (%s, %s)' % sensor_pos)
        self._window.writeln('my sensor value is %s' % sensor_val)

        self.win_function_dict = {
            "ping": self.exec_ping,
            "list": self.exec_list,
            "move": self.exec_move,
            "echo": self.exec_echo,
            "size": self.exec_size,
            "value": None,
            "sum": None,
            "min": None,
            "max": None,
            "quit": self._window.quit,
            "exit": self._window.quit,
            "help": self.helptext,
        }

        self.recv_funct_dict = {
            MSG_PING: self.recv_ping,
            MSG_PONG: self.recv_pong,
            MSG_ECHO: self.recv_echo,
            MSG_ECHO_REPLY: self.recv_echo_reply,
        }

        self.op_dict = {
            OP_SIZE: self.calc_sum,
            OP_SUM: self.calc_sum,
            OP_MIN: self.calc_min,
            OP_MAX: self.calc_max,
        }

        # Discover neighbours
        self.ping_timer = self._window._root.after(
            self.ping_period * 1000, self.exec_ping, [])
        self.exec_ping()

        # Start the main loop
        self.loop()

    def loop(self):
        # -- This is the event loop. --
        while self._window.update():

            # Handle the sockets
            input_ready, output_ready, except_ready = \
                select([self.mcast, self.peer], [], [], 0)
            for sock in input_ready:
                message = sock.recvfrom(1024)
                if not message:
                    # Source has disconnected
                    # TODO Remove source from list
                    pass

                # Decode the message
                msg_type, sequence, initiator, source, operation, \
                    payload = message_decode(message[0])
                recv_function_args = \
                    [sequence, initiator, source, operation, payload]

                # Call the respective function to handle the request
                try:
                    self.recv_funct_dict[msg_type](message[1],
                                                   *recv_function_args)
                except KeyError:
                    self._window.writeln('Unknown data received.')
                except IndexError:
                    self._window.writeln('To few arguments for: %s'
                                         % msg_type)

            # Handle the input from the user
            input_ln = self._window.getline()
            if input_ln:
                self._window.writeln(input_ln)
                try:
                    self.win_function_dict[input_ln.lower()]()
                except KeyError:
                    self._window.writeln('Unknown command.')
                except IndexError:
                    self._window.writeln('To few arguments for: %s' % input_ln)

    def exec_ping(self, *args):
        """
        Empty the neighbour list and execute a ping request
        """
        self._window._root.after_cancel(self.ping_timer)
        self.ping_timer = self._window._root.after(
            self.ping_period * 1000, self.exec_ping, [])

        self.neighbours = {}
        self._window.writeln("Refreshing list of all neighbours...")
        data = message_encode(MSG_PING, -1, self.sensor_pos, self.sensor_pos)
        self.peer.sendto(data, self.mcast_addr)

    def recv_ping(self, addr, *args):
        """
        When receiving a ping request, return a pong
        """
        if (len(args) != 5):
            self._window.writeln('Received incorrect data...')
            return

        # Ignoring ping message from self
        if (addr[1] == self.peer.getsockname()[1]):
            return

        # Check if in range
        source = args[2]
        dx = source[0] - self.sensor_pos[0]
        dy = source[1] - self.sensor_pos[1]
        distance = sqrt(pow(dx, 2) + pow(dy, 2))
        if (distance <= self.sensor_range):
            self._window.writeln('Received a ping message from (' +
                                 str(source[0]) + ',' + str(source[1]) +
                                 '), returning Pong...')
            # Send PONG
            data = message_encode(MSG_PONG, -1, source, self.sensor_pos)
            self.peer.sendto(data, addr)

    def recv_pong(self, addr, *args):
        """
        Register the pong sender as a neighbour
        """
        if (len(args) != 5):
            self._window.writeln('Received incorrect data...')
            return

        source = args[2]
        self._window.writeln('Received a pong message from (' + str(source[0])
                             + ',' + str(source[1]) + '), registering...')

        # Register neighbour
        self.neighbours[source] = addr

    def exec_list(self):
        """
        List all neighbours registered during ping
        """
        self._window.writeln("All current neighbours:")
        for location in self.neighbours:
            self._window.write(" - " + str(location) + ": " +
                               str(self.neighbours[location]) + "\n")

    def exec_move(self):
        sensor_pos = random_position(self.grid_size)
        self._window.writeln('my new position is (%s, %s)' % sensor_pos)
        self.sensor_pos = sensor_pos

    def exec_value(self):
        value = randint(0, 100)
        self._window.writeln('my new sensor value is %s' % value)
        self.sensor_val = value

    def exec_sum(self):
        self.send_echo(self.echo_sequence, self.sensor_pos, None,
                       OP_SUM, self.sensor_val)
        self.echo_sequence += 1

    def exec_min(self):
        self.send_echo(self.echo_sequence, self.sensor_pos, None,
                       OP_MIN, self.sensor_val)
        self.echo_sequence += 1

    def exec_max(self):
        self.send_echo(self.echo_sequence, self.sensor_pos, None,
                       OP_MAX, self.sensor_val)
        self.echo_sequence += 1

    def exec_size(self):
        self.send_echo(self.echo_sequence, self.sensor_pos, None, OP_SIZE, 1)
        self.echo_sequence += 1

    def calc_sum(self, value1, value2):
        return (value1 + value2)

    def calc_min(self, value1, value2):
        if value2 > value1:
            return value2
        else:
            return value1

    def calc_max(self, value1, value2):
        if value2 < value1:
            return value2
        else:
            return value1

    def exec_echo(self):
        """
        Abstraction layer for the gui interface echo command
        """
        self.send_echo(self.echo_sequence, self.sensor_pos, None, OP_NOOP)
        self.echo_sequence += 1

    def send_echo(self, sequence, initiator, father, operation=0, payload=0):
        """
        Send an ECHO command to all but the father
        """
        echo_id = (sequence, initiator)
        self.echo_tracking[echo_id] = deepcopy(self.neighbours)
        for position in self.neighbours:
            if father != position:
                data = message_encode(MSG_ECHO, sequence, initiator,
                                      self.sensor_pos, operation, payload)
                self.peer.sendto(data, self.neighbours[position])
            else:
                del self.echo_tracking[father]

    def recv_echo(self, addr, *args):
        if (len(args) != 5):
            self._window.writeln('Received incorrect data...')
            return

        # Create an echo ID with sequence and initialiser
        echo_id = args[0:2]
        source = args[2]
        payload = args[4]



        if echo_id in self.echos_recvd:
            payload = do_op(args[3], payload)
            # Already received so ECHO_REPLY
            # self.send_echo_reply(source)
            pass
        else:
            # Make sender father and add to echos_recvd
            father = source

            if len(self.neighbours) == 1:
                payload = do_op(args[3], payload)
                # No neighbours except for the father
                # self.send_echo_reply(father)
                print("replying")
            else:
                # Send on to neighbours
                self.send_echo(args[0], args[1], father, args[3], args[4])
                self.fathers[echo_id] = father
                self.echos_recvd.append(echo_id)

    def send_echo_reply(self, dest):
        pass

    def recv_echo_reply(self, addr, *args):
        if (len(args) != 5):
            self._window.writeln('Received incorrect data...')
            return

        # Create an echo ID with sequence and initialiser
        echo_id = args[0:2]

        # remove the sending neighbour from the list
        del self.echo_tracking[addr]

        # If all neighbours have responded, send back to the father
        if (len(self.neighbours) == 0):
            self.send_echo_reply(self.fathers[echo_id])
            del self.fathers[echo_id]
            self.echos_recvd.remove(echo_id)

    def helptext(self):
        # Required
        self._window.write('List of available commands:\n' +
                           ' - ping  : Sends a multicast ping message.\n' +
                           ' - list  : List all known neighbours.\n' +
                           ' - move  : Move node to random new position.\n' +
                           ' - echo  : Initiate echo wave.\n' +
                           ' - size  : Get the size of the network.\n' +
                           ' - exit  : Exit the node\n' +
                           ' - quit  : Exit the node\n')
        # Bonus
        self._window.write(' - value : New random sensor value.\n' +
                           ' - sum   : Sum all sensor values.\n' +
                           ' - min   : Minimum of all sensor values.\n' +
                           ' - max   : Maximum of all sensor values.\n')


# Get random position in NxN grid.
def random_position(n):
    x = randint(0, n)
    y = randint(0, n)
    return (x, y)


# -- program entry point --
if __name__ == '__main__':
    import sys
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('--group', help='multicast group', default='224.1.1.1')
    p.add_argument('--port', help='multicast port', default=50000, type=int)
    p.add_argument('--pos', help='x,y sensor position', default=None)
    p.add_argument('--grid', help='size of grid', default=100, type=int)
    p.add_argument('--range', help='sensor range', default=50, type=int)
    p.add_argument('--value', help='sensor value', default=-1, type=int)
    p.add_argument('--period', help='period between autopings (0=off)',
                   default=5, type=int)
    args = p.parse_args(sys.argv[1:])

    if args.pos:
        pos = tuple(int(n) for n in args.pos.split(',')[:2])
    else:
        pos = random_position(args.grid)

    if args.value >= 0:
        value = args.value
    else:
        value = randint(0, 100)

    mcast_addr = (args.group, args.port)
    SensorNode(mcast_addr, pos, args.range, value, args.grid, args.period)
