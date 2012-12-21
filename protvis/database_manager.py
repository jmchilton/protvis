from threading import Thread, Lock
import time
import os

from parameters import converted
from Common import test
import Reference

try:
    import sqlite3
except:
    print " * Failed to load sqlite3. Uploaded files will not be deleted automatically."


#Keeps track of every group of files uploaded, and deletes them after a set
#amount of time to free some space it also checks periodically to see if there
#has been any new jobs and adds them to its database this relies on the
#sqlite3 module. if it is not abaliable then the files wont be deleted
#automatically
class DatabaseManager(Thread):
    def __init__(self, name):
        Thread.__init__(self)
        try:
            sqlite3
        except:
            self.new = None
            return
        self.daemon = True
        self.name = name
        self.inserts = Lock()
        self.new = []

    def start(self):
        if self.new != None:
            Thread.start(self)

    #The monitoring thread
    def run(self):
        conn = sqlite3.connect(self.name)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS Uploads (file TEXT, date UNSIGNED BIG INT, expires INT, galaxy BOOLEAN, deleted BOOLEAN)")
        conn.commit()
        c.close()
        while True:
            for i in xrange(24 * 60):
                time.sleep(60)
                c = conn.cursor()
                self.inserts.acquire()
                for ins in self.new:
                    c.execute("INSERT INTO Uploads VALUES ('" + ins["name"] + "'," + ins["time"] + "," + ins["expires"] + "," + ins["galaxy"] + ",0)")
                self.new = []
                self.inserts.release()
                conn.commit()
                c.close()
            print "Performing daily cleanup..."
            if DatabaseManager._cleanup(conn) == 0:
                print "Nothing to clean up"
        conn.close()

    def insert(self, name, galaxy, expires=7 * 24 * 60 * 60):
        if self.new != None:
            self.inserts.acquire()
            self.new.append({"name": name, "time": str(int(time.mktime(time.gmtime()))), "expires": str(expires), "galaxy": str(test(galaxy, 1, 0))})
            self.inserts.release()

    @staticmethod
    #this is for use directly from the commandline
    def cleanup(name):
        try:
            sqlite3
        except:
            return
        conn = sqlite3.connect(name)
        if DatabaseManager._cleanup(conn) == 0:
            print "Nothing to clean up"
        conn.close()

    @staticmethod
    def _cleanup(conn):
        c = conn.cursor()
        c.execute("SELECT rowid, file FROM Uploads WHERE deleted=0 AND expires>0 AND date+expires<=" + str(int(time.mktime(time.gmtime()))))
        removed = 0
        for rowid, name in c:
            print "Removing " + name
            removed += 1
            fname = converted + name
            subsets = len(Reference.FileLinks(fname).Links)
            os.remove(fname)
            for i in xrange(subsets):
                try:
                    os.remove(fname + "_" + str(i))
                except:
                    if os.path.exists(fname + "_" + str(i)):
                        print "Failed to delete " + name + "_" + str(i)
            c.execute("UPDATE Uploads SET deleted=1 WHERE rowid=" + str(rowid))
        conn.commit()
        c.close()
        return removed
