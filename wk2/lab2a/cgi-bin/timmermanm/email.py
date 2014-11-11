## Netwerken en Systeembeveiliging Lab 2A - HTTP and SMTP
## NAME: Maico Timmerman
## STUDENT ID: 10542590
import os
import urlparse
import signal
import ssl
import base64
import datetime
from socket import socket
from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR


class SMTPClient():
    def __init__(self, query_dict):
        """
        The entry point of the HTTP server.
        port: The port to listen on.
        public_html: The directory where all static files are stored.
        cgibin: The directory where all CGI scripts are stored.
        """

        # Create the server
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        # Set env variables
        self.smtp_server = query_dict['server'][0]
        self.smtp_from = query_dict['from'][0]
        self.smtp_to = query_dict['to'][0]
        self.smtp_subject = query_dict['subject'][0]
        self.smtp_body = query_dict['body'][0]

        # Server credentials
        self.smtp_username = query_dict['username'][0]
        self.smtp_password = query_dict['password'][0]

        print('SMTPClient initialized, ready to start sending e-mail\n')

    def send_SMTP_mail(self):

        # Make initial contact
        self.init_connection()

        # STARTTLS session
        self.starttls()

        # SSL wrapping the socket
        print('Securing socket with SSL\n')
        self.client_socket = ssl.wrap_socket(self.client_socket)

        # Send EHLO to the server to identify ourselves.
        self.send_msg('EHLO example.server.com')

        # Send authentication
        self.auth_login(self.smtp_username, self.smtp_password)

        # Set mail fields
        self.send_msg('MAIL FROM: <{}>'.format(self.smtp_from))
        self.send_msg('RCPT TO: <{}>'.format(self.smtp_to))
        self.send_data(
            self.smtp_subject,
            self.smtp_from,
            self.smtp_to,
            self.smtp_body)

        # Exit the connection and therefor send the e-mail.
        self.send_quit()

    def init_connection(self):
        self.client_socket.connect((self.smtp_server, 587))
        request_data = self.client_socket.recv(1024)
        print('Response: {}'.format(request_data))

        # Check the response from the server for the expected response code
        if request_data[:3] != '220':
            raise Exception(
                '220 reply not received from server upon connection.')

    def starttls(self):
        print("Sending: {}".format('STARTTLS'))
        self.client_socket.send('STARTTLS\r\n')
        request_data = self.client_socket.recv(1024)
        print('Response: {}'.format(request_data))

        # Check the response from the server for the expected response code
        if request_data[:3] != '220':
            raise Exception(
                '220 reply not received from server upon init TLS.')

    def auth_login(self, username, password):

        print('Sending: AUTH LOGIN')
        self.client_socket.send('AUTH LOGIN\r\n')
        request_data = self.client_socket.recv(1024)
        print('Response: {}'.format(request_data))

        # Check the response from the server for the expected response code
        if request_data[:3] != '334':
            raise Exception(
                '334 reply not received from server upon init authentication.')

        # Send the username and check if the response is accepted
        print('Sending: username')
        self.client_socket.send(base64.b64encode(username)+'\r\n')
        request_data = self.client_socket.recv(1024)
        print('Response: {}'.format(request_data))

        # Check the response from the server for the expected response code
        if request_data[:3] != '334':
            raise Exception(
                '334 reply not received from server upon username check.')

        # Send the password and check if the response is "OK Authenticated"
        print('Sending: password')
        self.client_socket.send(base64.b64encode(password)+'\r\n')
        request_data = self.client_socket.recv(1024)
        print('Response: {}'.format(request_data))

        # Check the response from the server for the expected response code
        if request_data[:3] != '235':
            raise Exception(
                '235 reply not received from server upon authentication.')

    def send_msg(self, msg):
        print("Sending: {}".format(msg))
        self.client_socket.send(msg + '\r\n')
        request_data = self.client_socket.recv(1024)
        print('Response: {}'.format(request_data))

        # Check the response from the server for the expected response code
        if request_data[:3] != '250':
            raise Exception(
                '250 reply not received from server upon sending message.')

    def send_data(self, subject, send_from, send_to, body):

        # Prepare the server for data
        print("Sending: {}".format('DATA'))
        self.client_socket.send('DATA\r\n')
        request_data = self.client_socket.recv(1024)
        print('Response: {}'.format(request_data))

        # Check the response from the server for the expected response code
        if request_data[:3] != '354':
            raise Exception(
                '354 reply not received from server upon sending DATA.')

        send_data = ''
        send_data += 'Date: {}\r\n'.format(str(datetime.datetime.utcnow()))
        send_data += 'From: {}\r\n'.format(send_from)
        send_data += 'To: {}\r\n'.format(send_to)
        send_data += 'Subject: {}\r\n'.format(subject)
        send_data += '\r\n'
        send_data += '{}'.format(body)
        send_data += '\r\n.\r\n'

        print("Sending:\r\n{}".format(send_data))
        self.client_socket.send(send_data)
        request_data = self.client_socket.recv(1024)
        print('Response: {}'.format(request_data))

        # Check the response from the server for the expected response code
        if request_data[:3] != '250':
            raise Exception(
                '250 reply not received from server upon init TLS.')

    def send_quit(self):
        print("Sending: {}".format('QUIT'))
        self.client_socket.send('QUIT\r\n')
        request_data = self.client_socket.recv(1024)
        print('Response: {}'.format(request_data))

        # Check the response from the server for the expected response code
        if request_data[:3] != '221':
            raise Exception(
                '221 reply not received from server upon sending QUIT.')


def time_out_handler(signum, frame):
    raise Exception("Time-out")

# Converts the GET params to { key : [value] }
query_dict = urlparse.parse_qs(os.environ["QUERY_STRING"])

# Set a time-out handler for the smtp request.
signal.signal(signal.SIGALRM, time_out_handler)
signal.alarm(10)

# Initialize SMTP client to send an email
try:
    smtp_client = SMTPClient(query_dict)
except:
    print('Could not initialize the SMTPclient, incorrect parameters! :(')
    exit(1)

try:
    smtp_client.send_SMTP_mail()
except Exception as e:
    print('smtp_cleint.send_SMTP_mail(): ' + str(e) + '! :(')
    exit(1)
