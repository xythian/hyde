all: refresh

refresh:
	./hyde.py -g -s ./snorp.net

monitor:
	./hyde.py -k -g -s ./snorp.net
