from hashlib import sha1
import os
import struct
import tempfile
from threading import Thread, Lock
from urllib import urlretrieve

from database_manager import DatabaseManager
from conversion import Converter
import Reference
from parameters import converted
from Common import test, EncodeStringToFile


#Keeps track of all the uploads while they are going through the initial processing stage, both from galaxy and the web interface
class JobManager:

    def __init__(self):
        self.database_manager = DatabaseManager(converted + "sets.db")
        self.download_manager = DownloadManager()
        self.Jobs = {}
        self.NextJobID = 0
        self.ThreadsLock = Lock()

    def add_job(self, job_type, fs, cleanup, ref=Reference.LoadChainGroup):
        if job_type == "url":
            f = os.path.basename("%s_i" % self.download_manager.get_location(fs))
            data = open(f, "w")
        else:
            data = tempfile.NamedTemporaryFile(dir=".", prefix=converted, delete=False)
            f = data.name[len(converted):]
        self.ThreadsLock.acquire()
        try:
            jobid = self.NextJobID
            self.NextJobID += 1
            self.Jobs[jobid] = {"index": data, "file": f}
            thread_class = ReferenceThread
            if job_type == "remote":
                #add a job from the web interface uploader
                stream = True
                file_data = [[upload.filename, upload.file] for upload in fs]
            elif job_type == "local":
                #add a job from galaxy
                stream = False
                file_data = fs
            elif job_type == "url":
                stream = False
                file_data = fs
                thread_class = UrlReferenceThread
            self.Jobs[jobid]["ref"] = thread_class(self, self.Jobs[jobid], file_data, data, ref, self.ThreadsLock, stream, cleanup)
            self.Jobs[jobid]["ref"].start()
            return (jobid, f)
        finally:
            self.ThreadsLock.release()

    def start(self):
        self.database_manager.start()

    #check the status of a job to see if it has finished, or how many tasks
    #are remaining if the job has finished, it updates the index file for the
    #dataset with the correct information
    def QueryStatus(self, f, jobid):
        self.ThreadsLock.acquire()
        try:
            try:
                job = self.Jobs[jobid]
            except:
                raise
            if job["file"] != f:
                raise ValueError()
            if "files" in job:  # converting files
                alive = self.__threads_alive(job)
                if alive == 0:
                    self.__write_index_file(job)
                    del self.Jobs[jobid]
                return alive
            else:  # still loading up the links
                return -1
        finally:
            self.ThreadsLock.release()

    def __threads_alive(self, job):  # Has ThreadsLock
        alive = 0
        for t, _ in job["files"]:
            if t != None:
                if not t.started() or t.is_alive():
                    alive += 1
        return alive

    def __write_index_file(self, job):  # Has ThreadsLock
        #write the index file
        data = job["index"]
        fs = 0
        dbs = 0
        files = job["files"]
        for t, f in files:
            if t != None and t.Type() > f.Type:
                f.Type = t.Type()
            if (f.Type & ~Reference.FileType.MISSING) == Reference.FileType.DATABASE:
                dbs += 1
            else:
                fs += 1
        data.write(struct.pack("=II", fs, dbs))
        for t, f in files:
            if (f.Type & ~Reference.FileType.MISSING) != Reference.FileType.DATABASE:
                data.write(struct.pack("=BH", f.Type, len(f.Depends)))
                for d in f.Depends:
                    data.write(struct.pack("=H", test(d < 0, 0xFFFF, d)))
                EncodeStringToFile(data, f.Name)
        for t, f in files:
            if (f.Type & ~Reference.FileType.MISSING) == Reference.FileType.DATABASE:
                EncodeStringToFile(data, f.Name)
        data.close()


#This class takes care of the referencing stage of the processing
class ReferenceThread(Thread):
    def __init__(self, job_manager, job, f, data, ref, lock, stream, cleanup):
        """
        job --
        f -- List of file names and file objects(?)
        data --
        ref --
        lock -- JobManager.ThreadsLock
        stream --
        cleanup -- Lifetime of cache.
        """
        Thread.__init__(self)
        self.job_manager = job_manager
        self.job = job
        self.file = f
        self.data = data
        self.ref = ref
        self.lock = lock
        self.stream = stream
        self.cleanup = cleanup

    def run(self):
        files = self.ref(self.file)
        threads = range(len(files))
        links = {}
        for i in threads:
            links[files[i].Name] = i
        #Now generate all the data files
        data_name = self.data if isinstance(self.data, str) else self.data.name
        for i in threads:
            f = files[i]
            if f.Type & Reference.FileType.MISSING:
                threads[i] = None
            else:
                p = Reference.GetTypeParser(f.Type)
                if p == None:
                    thread = None
                else:
                    dest = data_name + "_" + str(i)
                    if os.path.exists(dest):
                        thread = None
                    elif self.stream:
                        thread = Converter(p, f.Stream, dest, f.Name)
                    else:
                        thread = Converter(p, f.Name, dest, f.Name)
                if thread:
                    thread.start()
                threads[i] = thread
        f = data_name[len(converted):]
        self.job_manager.database_manager.insert(f, True, self.cleanup)
        self.lock.acquire()
        self.job["files"] = [[threads[i], files[i]] for i in xrange(len(threads))]
        self.lock.release()


class DownloadManager:

    def __init__(self):
        self.url_locks = {}
        self.lock = Lock()

    def get_location(self, url):
        return converted + sha1(url).hexdigest()

    def download(self, url):
        location = self.get_location(url)
        url_lock = self.__acquire_url_lock(url, location)
        try:
            return self.__download_with_url_lock(url, location, url_lock)
        finally:
            self.__release_url_lock(location)

    def __download_with_url_lock(self, url, location, url_lock):
        url_lock.acquire()
        try:
            if not os.path.exists(location):
                try:
                    urlretrieve(url, location)
                    return location
                except:
                    os.remove(location)
                    raise
            return location
        finally:
            url_lock.release()

    def __acquire_url_lock(self, url, location):
        self.lock.acquire()
        try:
            if location not in self.url_locks:
                self.url_locks[location] = Lock()
            url_lock = self.url_locks[location]
        finally:
            self.lock.release()
        return url_lock

    def __release_url_lock(self, location):
        self.lock.acquire()
        try:
            del self.url_locks[location]
        finally:
            self.lock.release()
        return location


class UrlReferenceThread(ReferenceThread):

    def __init__(self, job_manager, job, url, data, ref, lock, stream, cleanup):
        super(UrlReferenceThread, self).__init__(job_manager, job, None, data, ref, lock, stream, cleanup)
        self.url = url

    def run(self):
        self.file = self.job_manager.download_manager.download(self.url)
        #self.data = "%s_i" % self.file
        super(UrlReferenceThread, self).run()


Jobs = JobManager()
