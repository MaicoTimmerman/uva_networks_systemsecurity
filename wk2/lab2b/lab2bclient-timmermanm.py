## Netwerken en Systeembeveiliging Lab 2B - Chat Room (Client)
## NAME:
## STUDENT ID:
from gui import MainWindow

def loop(port, cert):
	"""
	GUI loop.
	port: port to connect to.
	cert: public certificate (bonus task)
	"""
	# The following code explains how to use the GUI.
	w = MainWindow()
	# update() returns false when the user quits or presses escape.
	while w.update():
		# if the user entered a line getline() returns a string.
		line = w.getline()
		if line:
			w.writeln(line)



## Command line parser.
if __name__ == '__main__':
	import sys, argparse
	p = argparse.ArgumentParser()
	p.add_argument('--port', help='port to connect to', default=12345, type=int)
	p.add_argument('--cert', help='server public cert', default='')
	args = p.parse_args(sys.argv[1:])
	loop(args.port, args.cert)

