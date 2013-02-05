import platform
from threading import Thread
import Reference
from multiprocessing import Process, Queue


#The top level function for converting files
def Converter(mod, src, dst, name):
    if platform.system() == "Windows":
        #windows cannot handle the seperate processes, and so we must use
        #seperate threads this is much slower, but the only way
        return ConverterThread(mod, src, dst, name)
    else:
        #linux/OSX can have a sperate process for each task, and can perform
        #many tasks at once
        return SpawnConvertProcess(mod, src, dst, name)


#the converter for windows
#uses the threading module, which can only perform 1 task at a time
class ConverterThread(Thread):
    def __init__(self, mod, src, dst, name):
        Thread.__init__(self)
        self.Source = src
        self.Dest = dst
        self.Module = mod
        self.Name = name
        self.Type = Reference.FileType.UNKNOWN

    def started(self):
        return self.ident != None

    def run(self):
        (self.Source, close) = _ready_source_file(self.Source, self.Dest, self.Module)
        try:
            self.Type = self.Module.ToBinary(self.Source, self.Dest, self.Name)
        finally:
            if close:
                self.Source.close()


#the converter for unix
#uses the processing module, which can process any number of tasks at a time
def SpawnConvertProcess(mod, src, dst, name):
    class _ConvertProcess(Process):
        def __init__(self, *args, **kwargs):
            self.q = Queue()
            kwargs["args"] += (self.q,)
            Process.__init__(self, *args, **kwargs)
            self._type = None
            #self.Type = Reference.FileType.UNKNOWN

        def started(self):
            return self.pid != None

        def run(self):
            Process.run(self)
            #self.Type = self.q.get()

        def Type(self):
            if self._type == None:
                self._type = self.q.get()
            return self._type

    return _ConvertProcess(target=ConvertProcess, args=(mod, src, dst, name))


#The entry point function for processes created with the above class
def ConvertProcess(mod, src, dst, name, q):
    (src, close) = _ready_source_file(src, dst, mod)
    try:
        q.put(mod.ToBinary(src, dst, name))
    finally:
        if close:
            src.close()


def _ready_source_file(source, destination, module):
    convert = getattr(module, "DO_CONVERT", True)
    close = False
    if convert:
        if type(source) != file:
            source = open(source, "r")
            close = True
        else:
            source.seek(0)
    return (source, close)
