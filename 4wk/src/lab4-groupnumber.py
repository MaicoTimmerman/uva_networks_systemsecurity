## Netwerken en Systeembeveiliging Lab 4 - Distributed Sensor Network
## NAME: Robin Klusman & Maico Timmerman
## STUDENT ID:
import struct
import select
from socket import socket, inet_aton
from socket import AF_INET, SO_REUSEADDR, SOL_SOCKET, SOCK_DGRAM, \
    IPPROTO_UDP, INADDR_ANY, IPPROTO_IP, IP_ADD_MEMBERSHIP, IP_MULTICAST_TTL
from random import randint
from gui import MainWindow


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
        # -- Create the multicast listener socket. --
        self.mcast = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)

        # Sets the socket address as reusable so you can run multiple instances
        # of the program on the same machine at the same time.
        self.mcast.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        # Subscribe the socket to multicast messages from the given address.
        self.mreq = struct.pack('4sl',
                                inet_aton(mcast_addr[0]),
                                INADDR_ANY)
        self.mcast.setsockopt(IPPROTO_IP,
                              IP_ADD_MEMBERSHIP,
                              self.mreq)
        self.mcast.bind(mcast_addr)

        # -- Create the peer-to-peer socket. --
        self.peer = socket(AF_INET,
                           SOCK_DGRAM,
                           IPPROTO_UDP)
        # Set the socket multicast TTL so it can send multicast messages.
        self.peer.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, 5)

        # Bind the socket to a random port.
        if sys.platform == 'win32':  # windows special case
            self.peer.bind(('localhost', INADDR_ANY))
        else:  # should work for everything else
            self.peer.bind(('', INADDR_ANY))

        # -- make the gui --
        self._window = MainWindow()
        self._window.writeln('my address is %s:%s' % self.peer.getsockname())
        self._window.writeln('my position is (%s, %s)' % sensor_pos)
        self._window.writeln('my sensor value is %s' % sensor_val)

        function_dict = {
            "ping": self.ping_cmd,
            "list": self.list_cmd,
            "move": self.move_cmd,
            "echo": self.echo_cmd,
            "size": self.size_cmd,
            "value": None,
            "sum": None,
            "min": None,
            "max": None,
            "quit": self._window.quit,
            "exit": self._window.quit,
            "help": self.helptext,
        }

        # -- This is the event loop. --
        while self._window.update():
            input_ready, output_ready, except_ready = \
                select([self.mcast, self.peer], [], [], 0)
            for rdy_socket in input_ready:
                data = rdy_socket.recv(1024)
                if not data:
                    # Source has disconnected
                    # TODO Remove source from list, or re-scan
                    pass
                else:
                    # TODO Check what we received and do the appropriate action
                    pass

            message = self._window.getline()
            if message:
                self._window.writeln(message)
                self._args = []
                try:
                    function_dict[message.lower()](*self._args)
                except KeyError:
                    self._window.writeln('Unknown command.')
                except IndexError:
                    self._window.writeln('To few arguments for: %s' % message)
                except TypeError:
                    self._window.writeln('Not implemented: %s' % message)

    def ping_cmd(self):
        self._window.writeln("Im now doing ping")
        pass

    def list_cmd(self):
        self._window.writeln("Im now doing list")
        self.neighbours  # = ...

        pass

    def move_cmd(self):
        self._window.writeln("Im now doing move")
        pass

    def echo_cmd(self):
        self.list_cmd()
        i = 0
        while self.neighbours[i]:
            # Echo neighbour
            i += 1

        self._window.writeln("Im now doing echo")
        pass

    def size_cmd(self):
        self._window.writeln("Im now doing size")
        pass

    def helptext(self):
        # Required
        self._window.write('List of available commands:\n' +
                           'ping  : Sends a multicast ping message.\n' +
                           'list  : List all known neighbours.\n' +
                           'move  : Move this node to random new position.\n' +
                           'echo  : Initiate echo wave.\n' +
                           'size  : Get the size of the network.\n' +
                           'exit  : Exit the node\n' +
                           'quit  : Exit the node\n')
        # Bonus
        self._window.write('value : New random sensor value.\n' +
                           'sum   : Sum all sensor values.\n' +
                           'min   : Minimum of all sensor values.\n' +
                           'max   : Maximum of all sensor values.\n')


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
