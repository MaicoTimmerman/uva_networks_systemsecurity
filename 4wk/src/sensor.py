## Netwerken en Systeembeveiliging
## Lab 4 - Distributed Sensor Network
## Definitions and message format
## Author: Robin Klusman & Maico Timmerman
import struct

## These are the message types.
MSG_PING = 0  # Multicast ping.
MSG_PONG = 1  # Unicast pong.
MSG_ECHO = 2  # Unicast echo.
MSG_ECHO_REPLY = 3  # Unicast echo reply.

## These are the echo operations.
OP_NOOP = 0  # Do nothing.
OP_SIZE = 1  # Compute the size of network.
OP_SUM = 2  # Compute the sum of all sensor values.
OP_MIN = 3  # Compute the lowest sensor value.
OP_MAX = 4  # Compute the highest sensor value.

## This is used to pack message fields into a binary format.
message_format = struct.Struct('!7if')

## Length of a message in bytes.
message_length = message_format.size


def message_encode(msg_type, sequence, initiator, neighbour,
                   operation=0, payload=0):
    """
    Encodes message fields into a binary format.

    msg_type: The message type.
    sequence: The wave sequence number.
    initiator: An (x, y) tuple that contains the initiator's position.
    neighbour: An (x, y) tuple that contains the neighbour's position.
    operation: The echo operation.
    payload: Echo operation data (a number).

    Returns: A binary string in which all parameters are packed.
    """
    ix, iy = initiator
    nx, ny = neighbour
    return message_format.pack(msg_type, sequence,
                               ix, iy, nx, ny, operation, payload)


def message_decode(bin_data):
    """
    Decodes a binary message string to Python objects.
    bin_data: The binary string to decode.
    Returns: A tuple containing all the unpacked message fields.
    """
    msg_type, sequence, ix, iy, nx, ny, operation, payload = \
        message_format.unpack(bin_data)
    return (msg_type, sequence, (ix, iy), (nx, ny), operation, payload)
