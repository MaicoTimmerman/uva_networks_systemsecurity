## Netwerken en Systeembeveiliging Lab 4 - Distributed Sensor Network
## NAME: Robin Klusman & Maico Timmerman
## STUDENT ID:
import struct
import socket
from random import randint
from gui import MainWindow


# Get random position in NxN grid.
def random_position(n):
    x = randint(0, n)
    y = randint(0, n)
    return (x, y)


def main(mcast_addr,
         sensor_pos, sensor_range, sensor_val,
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
    mcast = socket.socket(socket.AF_INET,
                          socket.SOCK_DGRAM,
                          socket.IPPROTO_UDP)
    # Sets the socket address as reusable so you can run multiple instances
    # of the program on the same machine at the same time.
    mcast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Subscribe the socket to multicast messages from the given address.
    mreq = struct.pack('4sl',
                       socket.inet_aton(mcast_addr[0]),
                       socket.INADDR_ANY)
    mcast.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    mcast.bind(mcast_addr)

    # -- Create the peer-to-peer socket. --
    peer = socket.socket(socket.AF_INET,
                         socket.SOCK_DGRAM,
                         socket.IPPROTO_UDP)
    # Set the socket multicast TTL so it can send multicast messages.
    peer.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 5)
    # Bind the socket to a random port.
    if sys.platform == 'win32':  # windows special case
        peer.bind(('localhost', socket.INADDR_ANY))
    else:  # should work for everything else
        peer.bind(('', socket.INADDR_ANY))

    # -- make the gui --
    window = MainWindow()
    window.writeln('my address is %s:%s' % peer.getsockname())
    window.writeln('my position is (%s, %s)' % sensor_pos)
    window.writeln('my sensor value is %s' % sensor_val)

    # -- This is the event loop. --
    while window.update():
        message = window.getline()
        if message:
            if message == 'ping':
                window.write('ping.\n')
                ping_cmd()
                pass
            elif message == 'list':
                window.write('list.\n')
                list_cmd()
                pass
            elif message == 'move':
                window.write('move.\n')
                move_cmd()
                pass
            elif message == 'echo':
                window.write('echo.\n')
                echo_cmd()
                pass
            elif message == 'size':
                window.write('size.\n')
                size_cmd()
                pass

            elif message == 'value':  # Bonus
                window.write('value.\n')
                pass
            elif message == 'min':    # Bonus
                window.write('min.\n')
                pass
            elif message == 'max':    # Bonus
                window.write('max.\n')
                pass

            elif message == 'quit' or message == 'exit':
                window.write('Exiting..\n')
                window.quit()
            else:
                window.write('Unknown command.\n')
                helptext(window)
        pass


def ping_cmd():
    pass


def list_cmd():
    pass


def move_cmd():
    pass


def echo_cmd():
    pass


def size_cmd():
    pass


def helptext(window):
    # Required
    window.write('List of available commands:\n' +
                 'ping  : Sends a multicast ping message.\n' +
                 'list  : List all known neighbours.\n' +
                 'move  : Move this node to random new position.\n' +
                 'echo  : Initiate echo wave.\n' +
                 'size  : Get the size of the network.\n')
    # Bonus
    window.write('value : New random sensor value.\n' +
                 'sum   : Sum all sensor values.\n' +
                 'min   : Minimum of all sensor values.\n' +
                 'max   : Maximum of all sensor values.\n')


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
    main(mcast_addr, pos, args.range, value, args.grid, args.period)
