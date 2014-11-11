## Netwerken en Systeembeveiliging Lab 2A - HTTP and SMTP
## NAME: Maico Timmerman
## STUDENT ID: 10542590


import signal
import mimetypes
import subprocess
from socket import socket
from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, SHUT_RDWR

PAGE_REGEX = u"GET (\S*) HTTP/1.1"


class Server():
    def __init__(self, port, public_html, cgibin, indexfile):
        """
        The entry point of the HTTP server.
        port: The port to listen on.
        public_html: The directory where all static files are stored.
        cgibin: The directory where all CGI scripts are stored.
        """

        # Create the server
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_socket.bind(('', port))
        self.server_socket.listen(1)

        # Set env variables
        self.public_html = public_html
        self.cgibin = cgibin
        self.indexfile = indexfile

        print('The server is ready to receive')

    def start(self):
        """ Main function of the webserver """
        while True:
            # Accept a new connection
            con_socket, addr = self.server_socket.accept()

            # Decode the request to a string
            request_data = con_socket.recv(1024)
            request_str = bytes.decode(request_data)

            # Only supports GET requests
            if (request_str.split(' ')[0] == 'GET'):
                request_file = request_str.split(' ')[1]

                # Serve the file, 200 if OK and 404 if Not Found
                if (request_file.startswith("/cgi-bin")):
                    self._cgi_serve(request_str, con_socket, request_file[8:])
                else:
                    self._serve(request_str, con_socket, request_file)
            else:
                self._abort_501(con_socket)

            con_socket.close()

    def stop(self):
        """ Shut down the server """
        try:
            print("Shutting down the server")
            self.server_socket.shutdown(SHUT_RDWR)
        except Exception as e:
            print("Warning: could not shut down the socket.", e)

    def _cgi_serve(self, request, con_socket, file_name):

        print('Using CGI_SERVE')

        # Create the file path by removing the GET params and saving them.
        request_file_path = self.cgibin + file_name
        request_file_path = request_file_path.split('?')[0]
        request_args = file_name.split('?')[1:]

        # If the file exists, start building a env to start the program.
        if (os.path.isfile(request_file_path)):

            print("File exists")

            cgi_command = ['python', str(request_file_path)]
            cgi_env = {}
            cgi_env["PATH"] = os.environ["PATH"]
            cgi_env["DOCUMENT_ROOT"] = str(self.public_html)
            cgi_env["REQUEST_METHOD"] = str(request.split(' ')[0])
            cgi_env["REQUEST_URI"] = str(request_file_path)
            if (request_args):
                cgi_env["QUERY_STRING"] = request_args[0]
            else:
                cgi_env["QUERY_STRING"] = ''

            # Execute the program from the request
            proc = subprocess.Popen(
                args=cgi_command,
                env=cgi_env,
                stdout=subprocess.PIPE)
            proc_stdout, proc_stderr = proc.communicate()

            # Return the results of the script executed
            response_header = self._gen_headers(200, len(proc_stdout),
                                                'text/plain')
            con_socket.send(response_header.encode() + proc_stdout)
        else:
            self._abort_404(con_socket)

    def _serve(self, request, con_socket, file_name):

        request_file_path = None

        # If the root of the site is requested, return the index.html
        if (file_name == "/"):
            request_file_path = self.indexfile
        else:
            request_file_path = self.public_html + file_name

        # Remove unneccesary GET params for normal files
        request_file_path = request_file_path.split('?')[0]
        print(request_file_path)

        # If a match has been found in the header, try to open the file

        if (os.path.isfile(request_file_path)):
            print("File found!")
            response_content = read_file(request_file_path)
            response_header = self._gen_headers(
                200,
                len(response_content),
                mimetypes.guess_type(request_file_path)[0])
            con_socket.send(response_header.encode() + response_content)
        else:
            self._abort_404(con_socket)

    def _abort_404(self, con_socket):
        """ Return a 404 page with headers """
        response_content = """
        <html>
        <head><title>404: Page not found!</title></head>
        <body>
        I could not find your page :(
        </body>
        </html>
        """
        response_header = self._gen_headers(404, len(response_content), 'html')
        con_socket.send(response_header.encode() + response_content)

    def _abort_501(self, con_socket):
        """ Return a 501 page with headers """
        response_content = """
        <html>
        <head><title>501: Sorry I don't understand!</title></head>
        <body>
        I dont understand!
        </body>
        </html>
        """
        response_header = self._gen_headers(501, len(response_content),
                                            'text/html')
        con_socket.send(response_header.encode() + response_content)

    def _gen_headers(self, status_code, content_length, content_type):

        header = ''

        # Http response code
        if (status_code == 200):
            header = 'HTTP/1.1 200 OK\r\n'
        elif (status_code == 404):
            header = 'HTTP/1.1 404 Not Found\r\n'
        elif (status_code == 501):
            header = 'HTTP/1.1 501 Not Implemented\r\n'

        # Content Type (guessed by mimetype)
        header += 'Connection: close\r\n'
        header += 'Content-Length: ' + str(content_length) + '\r\n'
        header += 'Content-Type: ' + content_type + '\r\n\r\n'
        print(header)
        return header


def sig_int(signal, frame):
    server.stop()
    exit(1)


def read_file(path):
    with open(str(path), 'rb') as f:
        return f.read()

## This the entry point of the script.
## Do not change this part.
if __name__ == '__main__':
    import os
    import sys
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--port',
                   help='port to bind to',
                   default=8080, type=int)
    p.add_argument('--public_html',
                   help='home directory',
                   default='./public_html')
    p.add_argument('--cgibin',
                   help='cgi-bin directory',
                   default='./cgi-bin')
    p.add_argument('--indexfile',
                   help='indexfile for root(from webserver root)',
                   default='/index.html')

    # Parse arguments
    args = p.parse_args(sys.argv[1:])
    public_html = os.path.abspath(args.public_html)
    cgibin = os.path.abspath(args.cgibin)
    indexfile = os.path.abspath(public_html + args.indexfile)

    # Start the server
    server = Server(args.port, public_html, cgibin, indexfile)
    server.start()

    # Stop the server
    signal.signal(signal.SIGINT, sig_int)
