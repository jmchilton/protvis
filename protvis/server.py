#!/usr/bin/python
"""
Usage:

    env/bin/python protvis/server.py $address $port $pass

Main driver program for when server starts with above command-line.

"""
from protvis import converted, main
from protvis.database_manager import DatabaseManager
from wsgiref.simple_server import make_server
from os.path import join
import sys


def start_server():
    #check to make sure everything is set up properly
    if "cleanup" in sys.argv:
        DatabaseManager.cleanup(join(converted, "sets.db"))
    else:
        if len(sys.argv) < 3:
            print "Usage: " + sys.argv[0] + " <ip address> <port>"
            exit(0)
        app = main()
        server = make_server(sys.argv[1], int(sys.argv[2]), app)
        print "Server is going up now"
        server.serve_forever()


if __name__ == "__main__":
    start_server()
