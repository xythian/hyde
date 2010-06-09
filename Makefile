all: refresh

refresh:
	./hyde.py -g -s ./snorp.net

monitor:
	./hyde.py -k -g -s ./snorp.net

push: refresh
	rsync -avz snorp.net/deploy/ snorp.net:~/snorp.net-www
