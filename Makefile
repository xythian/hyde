all: refresh

refresh:
	./hyde.py -g -s ./snorp.net

run: refresh
	./hyde.py -k -w -s ./snorp.net