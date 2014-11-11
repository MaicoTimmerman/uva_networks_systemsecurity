## Netwerken en Systeembeveiliging Lab 2B - Chat Room (Server)
## NAME:
## STUDENT ID:

def serve(port):
	"""
	Chat server entry point.
	port: The port to listen on.
	"""
	pass


## Command line parser.
if __name__ == '__main__':
	import sys, argparse
	p = argparse.ArgumentParser()
	p.add_argument('--port', help='port to listen on', default=12345, type=int)
	args = p.parse_args(sys.argv[1:])
	serve(args.port)

