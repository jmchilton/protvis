#!/usr/bin/python
from protvis import *

if __name__ == "__main__":
	#check to make sure everything is set up properly
	if "cleanup" in sys.argv:
		Database.cleanup(converted + "sets.db")
	else:
		if len(sys.argv) < 3:
			print "Usage: " + sys.argv[0] + " <ip address> <port>"
			exit(0)
		app = main()
		server = make_server(sys.argv[1], int(sys.argv[2]), app)
		print "Server is going up now"
		server.serve_forever()
